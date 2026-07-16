from domain.config.database_config import db
from domain.repositories.data_processing.postal_agencies import PostalAgencies

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from pyspark.sql import functions as F

import logging
import gc

logger = logging.getLogger(__name__)


class SavePostalAgenciesService:

    @staticmethod
    def upsert_postal_agencies_spark_df_to_db(
        spark_df,
        batch_size: int = 1
    ):

        expected_cols = {

            "name",
            "address",
            "district",
            "city",
            "state",
            "zip_code",
            "phone",
            "latitude",
            "longitude",
            "location"

        }

        missing = expected_cols - set(spark_df.columns)

        if missing:

            logger.warning(
                f"Spark DataFrame is missing expected columns: {missing}. "
                "Attempting to continue with available columns."
            )

        ###################################################################
        # valida POINT
        ###################################################################

        cleaned = spark_df.withColumn(
            "location_no_wrapper",
            F.regexp_replace(
                F.col("location"),
                r"^\s*(SRID=4326;)?POINT\s*\(",
                ""
            )
        ).withColumn(
            "location_no_wrapper",
            F.regexp_replace(
                F.col("location_no_wrapper"),
                r"\)\s*$",
                ""
            )
        )

        cleaned = cleaned.withColumn(

            "coords",

            F.split(
                F.col("location_no_wrapper"),
                r"\s+"
            )

        )

        valid_df = cleaned.filter(
            F.size("coords") == 2
        )

        invalid_count = cleaned.filter(
            F.size("coords") != 2
        ).count()

        if invalid_count > 0:

            logger.warning(
                f"Filtered out {invalid_count} invalid POINT geometries."
            )

        ###################################################################
        # casts
        ###################################################################

        cast_cols = [

            "name",
            "address",
            "district",
            "city",
            "state",
            "zip_code",
            "phone",
            "location"

        ]

        for c in cast_cols:

            if c in valid_df.columns:

                valid_df = valid_df.withColumn(
                    c,
                    F.col(c).cast("string")
                )

        if "latitude" in valid_df.columns:

            valid_df = valid_df.withColumn(
                "latitude",
                F.col("latitude").cast("double")
            )

        if "longitude" in valid_df.columns:

            valid_df = valid_df.withColumn(
                "longitude",
                F.col("longitude").cast("double")
            )

        ###################################################################
        # iterator
        ###################################################################

        iterator = valid_df.toLocalIterator()

        processed = 0

        inserted_or_updated = 0

        updatable_cols = [

            c.name

            for c in PostalAgencies.__table__.columns

            if c.name != "primary_key"

        ]

        ###################################################################
        # row mapper
        ###################################################################

        def row_to_db_dict_once(row):

            r = row.asDict()

            return {

                "name":
                    r.get("name"),

                "address":
                    r.get("address"),

                "district":
                    r.get("district"),

                "city":
                    r.get("city"),

                "state":
                    r.get("state"),

                "zip_code":
                    r.get("zip_code"),

                "phone":
                    r.get("phone"),

                "latitude":
                    float(r["latitude"])
                    if r.get("latitude") is not None
                    else None,

                "longitude":
                    float(r["longitude"])
                    if r.get("longitude") is not None
                    else None,

                "location":
                    r.get("location")

            }
        
        try:

            ###################################################################
            # batch_size == 1
            ###################################################################

            if batch_size == 1:

                for row in iterator:

                    processed += 1

                    db_row = row_to_db_dict_once(row)

                    try:

                        stmt = insert(
                            PostalAgencies
                        ).values(
                            db_row
                        )

                        update_dict = {

                            col: getattr(
                                stmt.excluded,
                                col
                            )

                            for col in updatable_cols

                        }

                        stmt = stmt.on_conflict_do_update(

                            constraint="unique_name_zip_code",

                            set_=update_dict

                        )

                        db.session.execute(stmt)

                        db.session.commit()

                        inserted_or_updated += 1

                    except SQLAlchemyError as e:

                        db.session.rollback()

                        logger.exception(

                            f"SQLAlchemy error while upserting row "
                            f"at processed={processed}: {e}"

                        )

                    except Exception as e:

                        db.session.rollback()

                        logger.exception(

                            f"Unexpected error while upserting row "
                            f"at processed={processed}: {e}"

                        )

                    finally:

                        try:

                            db.session.expunge_all()

                            db.session.close()

                        except Exception:

                            pass

                        del db_row

                    if processed % 200 == 0:

                        gc.collect()

                        logger.debug(

                            f"Periodic GC at processed={processed}"

                        )

            ###################################################################
            # batches
            ###################################################################

            else:

                batch = []

                for row in iterator:

                    processed += 1

                    db_row = row_to_db_dict_once(row)

                    batch.append(db_row)

                    del db_row

                    if len(batch) >= batch_size:

                        try:

                            stmt = insert(
                                PostalAgencies
                            ).values(
                                batch
                            )

                            update_dict = {

                                col: getattr(
                                    stmt.excluded,
                                    col
                                )

                                for col in updatable_cols

                            }

                            stmt = stmt.on_conflict_do_update(

                                constraint="unique_name_zip_code",

                                set_=update_dict

                            )

                            db.session.execute(stmt)

                            db.session.commit()

                            inserted_or_updated += len(batch)

                        except SQLAlchemyError as e:

                            db.session.rollback()

                            logger.exception(

                                f"SQLAlchemy error while "
                                f"upserting batch "
                                f"at processed={processed}: {e}"

                            )

                        except Exception as e:

                            db.session.rollback()

                            logger.exception(

                                f"Unexpected error while "
                                f"upserting batch "
                                f"at processed={processed}: {e}"

                            )

                        finally:

                            batch.clear()

                            gc.collect()

                            try:

                                db.session.expunge_all()

                                db.session.close()

                            except Exception:

                                pass
                        ###############################################################
                # Flush do último lote
                ###############################################################

                if batch:

                    try:

                        stmt = insert(
                            PostalAgencies
                        ).values(
                            batch
                        )

                        update_dict = {

                            col: getattr(
                                stmt.excluded,
                                col
                            )

                            for col in updatable_cols

                        }

                        stmt = stmt.on_conflict_do_update(

                            constraint="unique_name_zip_code",

                            set_=update_dict

                        )

                        db.session.execute(stmt)

                        db.session.commit()

                        inserted_or_updated += len(batch)

                    except SQLAlchemyError as e:

                        db.session.rollback()

                        logger.exception(

                            f"SQLAlchemy error on final batch: {e}"

                        )

                    except Exception as e:

                        db.session.rollback()

                        logger.exception(

                            f"Unexpected error on final batch: {e}"

                        )

                    finally:

                        batch.clear()

                        try:

                            db.session.expunge_all()

                            db.session.close()

                        except Exception:

                            pass

                        del batch

                        gc.collect()

        except Exception as e:

            logger.exception(

                f"Error while iterating Spark rows: {e}"

            )

        finally:

            ###############################################################
            # libera DataFrames do Spark
            ###############################################################

            try:

                cleaned.unpersist(
                    blocking=False
                )

            except Exception:

                pass

            try:

                valid_df.unpersist(
                    blocking=False
                )

            except Exception:

                pass

            ###############################################################
            # encerra sessão SQLAlchemy
            ###############################################################

            try:

                db.session.remove()

            except Exception:

                try:

                    db.session.close()

                except Exception:

                    pass

            ###############################################################
            # limpeza de memória
            ###############################################################

            try:

                del iterator
            except Exception:
                pass

            try:

                del cleaned

            except Exception:

                pass

            try:

                del valid_df

            except Exception:

                pass

            gc.collect()

            logger.info(

                "Completed streaming. "

                f"Processed {processed} valid rows; "

                f"upserted {inserted_or_updated} rows. "

                f"Invalid rows filtered: {invalid_count}."

            )
            
            return {

                "processed_rows": processed,

                "upserted_rows": inserted_or_updated,

                "invalid_rows_filtered": invalid_count

            }
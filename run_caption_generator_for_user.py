import os
from caption_generator import CaptionGenerator
from database import init_database, get_db, close_database
from loguru import logger

# Basic logger setup
logger.add("logs/caption_test.log", rotation="10 MB")

def run_generation_from_db():
    """
    Fetches jobs from MongoDB and generates captions.
    """
    logger.info("Initializing database...")
    try:
        init_database()
        db_manager = get_db()
        jobs_collection = db_manager.get_collection('jobs_clean')
        
        # Fetch the 4 most recent jobs
        # Assuming recency is based on insertion order, which is the default for _id
        jobs_to_process = list(jobs_collection.find().sort("_id", -1))
        
        if not jobs_to_process:
            logger.warning("No jobs found in the 'jobs_clean' collection.")
            return

        logger.info(f"Fetched {len(jobs_to_process)} jobs from the database.")

        logger.info("Initializing CaptionGenerator...")
        caption_gen = CaptionGenerator()
        logger.info("CaptionGenerator initialized.")

        # Generate captions
        captions = caption_gen.generate_captions(jobs_to_process)

        if captions:
            logger.success("Successfully generated captions!")
            output_file = "caption_output.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                for platform, caption in captions.items():
                    f.write(f"--- Platform: {platform} ---")
                    f.write(caption)
            print(f"Caption saved to {output_file}")
            logger.info(f"Caption saved to {output_file}")
        else:
            logger.warning("Caption generation returned no results.")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        logger.info("Closing database connection.")
        close_database()

if __name__ == "__main__":
    run_generation_from_db()

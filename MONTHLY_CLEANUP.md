# Monthly MongoDB Cleanup Strategy

## Overview

The Job Automation System includes a monthly cleanup feature to prevent database bloat and ensure fresh data. This is essential because:

- **RapidAPI/Jooble always return fresh job data**
- **Old job postings become irrelevant quickly**
- **Prevents storage bloat and performance issues**
- **Avoids duplicate posting problems**

## What Gets Cleaned

The monthly cleanup script clears these MongoDB collections:

- `raw_jobs` - Raw job data from APIs
- `clean_jobs` - Processed and filtered jobs
- `posts_ready` - Captions ready for posting
- `posted_items` - Successfully posted content

## How to Use

### Automatic Cleanup (Recommended)
Run the cleanup script monthly:

```bash
python monthly_cleanup.py
```

### Force Cleanup
If you need to clean up before the 30-day period:

```bash
python monthly_cleanup.py --force
```

### Windows Batch File
Use the provided batch file:

```bash
monthly_cleanup.bat
```

## Cleanup Logs

The script automatically logs all cleanup activities in the `cleanup_logs` collection:

- Timestamp of cleanup
- Number of documents deleted
- Collections cleared
- Action type

## Benefits

✅ **Fresh Data**: Always working with current job listings  
✅ **Performance**: Smaller database = faster queries  
✅ **Storage Efficiency**: Prevents unlimited growth  
✅ **No Duplicates**: Fresh start prevents old data issues  
✅ **Automated**: Can be scheduled to run monthly  

## Scheduling

You can schedule the cleanup to run automatically:

### Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Set to run monthly
4. Action: Start a program
5. Program: `python`
6. Arguments: `monthly_cleanup.py`

### Cron Job (Linux/Mac)
```bash
# Add to crontab - runs on 1st of every month at 2 AM
0 2 1 * * cd /path/to/automation && python monthly_cleanup.py
```

## Safety Features

- **Check Last Cleanup**: Script checks if 30 days have passed
- **Force Override**: Use `--force` flag to override time check
- **Logging**: All cleanup activities are logged
- **Error Handling**: Continues even if one collection fails

## After Cleanup

After running the cleanup:

1. **Fetch fresh jobs**: `python cli.py fetch`
2. **Generate captions**: `python cli.py generate-captions`
3. **Start posting**: `python cli.py post`

The system will work with completely fresh data from the APIs.


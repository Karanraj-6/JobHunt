# Job Automation System

An intelligent Python application that automatically fetches software engineering jobs from multiple sources, generates engaging captions using Google Gemini AI, creates AI-generated job posting images, and posts them to LinkedIn with optimal timing and engagement tracking.

## Features

- **Multi-Source Job Fetching**: Integrates with RapidAPI (Indeed) and Jooble for comprehensive job listings
- **AI-Powered Caption Generation**: Uses Google Gemini to create professional, engaging LinkedIn posts
- **AI Image Generation**: Creates custom job posting images with company logos and job details using Gemini
- **LinkedIn Automation**: Automated posting via Selenium with anti-detection measures
- **Smart Scheduling**: Intelligent posting schedule optimization based on engagement analytics
- **Database Management**: MongoDB support with comprehensive job tracking and analytics
- **Deduplication & Filtering**: Advanced job matching and filtering by skills, location, and seniority

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Job Sources   │    │  Job Processor   │    │  Caption Gen    │
│                 │    │                  │    │                 │
│ • RapidAPI      │───▶│ • Normalization  │───▶│ • Gemini AI     │
│ • Jooble        │    │ • Deduplication  │    │ • Style Config  │
│                 │    │ • Filtering      │    │ • Hashtags      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Database       │    │  Image Gen      │
                       │                  │    │                 │
                       │ • MongoDB       │    │ • Gemini Vision │
                       │ • Collections    │    │ • Company Logos │
                       │ • Indexes       │    │ • Job Details   │
                       │ • Analytics     │    │ • Fallback PIL  │
                       └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Scheduler      │    │  Social Poster  │
                       │                  │    │                 │
                       │ • APScheduler    │───▶│ • LinkedIn      │
                       │ • Cron Jobs      │    │ • Selenium      │
                       │ • Timezone       │    │ • Anti-Detection│
                       └──────────────────┘    └─────────────────┘
```

## Prerequisites

- Python 3.10+
- MongoDB 5.0+ (local or cloud instance)
- Chrome browser (for LinkedIn automation)
- Google Gemini API key
- RapidAPI key
- Jooble API key
- LinkedIn account credentials

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd job-automation
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup MongoDB**
   - **Local MongoDB**: Install and start MongoDB service
   - **Cloud MongoDB**: Use MongoDB Atlas or similar service
   - Update connection string in `.env` file

5. **Configure environment**
   ```bash
   cp env.template .env
   # Edit .env with your API keys and credentials
   ```

6. **Initialize database**
   ```bash
   python cli.py init
   ```

## Configuration

### Environment Variables (.env)

```bash
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=job_automation

# Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key_here

# LinkedIn Credentials
LINKEDIN_EMAIL=your_linkedin_email@example.com
LINKEDIN_PASSWORD=your_linkedin_password

# Job Sources
RAPIDAPI_KEY=your_rapidapi_key_here
JOOBLE_API_KEY=your_jooble_api_key_here
```

### Configuration File (config.yaml)

The application uses a YAML configuration file for:
- Job source preferences and API settings
- AI model settings (Gemini configuration)
- Image generation preferences
- Posting schedules and platform settings
- Database configuration
- Logging and monitoring settings

## Usage

### Command Line Interface

```bash
# Initialize database
python cli.py init

# Check system status
python cli.py status

# Manually fetch jobs
python cli.py fetch

# Manually post content
python cli.py post

# Start automated mode
python cli.py start

# Run system tests
python test_system.py

# Test Gemini integration
python test_gemini.py
```

### Automated Mode

The application can run in automated mode with:
- Scheduled job fetching (every 6 hours)
- Automated caption generation
- AI image creation
- Scheduled LinkedIn posting (9 AM and 6 PM IST)
- Engagement analytics collection

## Job Sources

### RapidAPI Integration
- **Indeed Jobs**: Comprehensive job listings with advanced filtering
- **Configurable Keywords**: Software engineering, Python, ML, Data Science
- **Rate Limiting**: Respects API limits with intelligent retry logic

### Jooble Integration
- **Global Job Aggregator**: Access to millions of job listings
- **Smart Filtering**: Location, skills, and experience-based filtering
- **Real-time Updates**: Fresh job postings as they become available

## AI Features

### Caption Generation
- **Google Gemini Integration**: Advanced AI-powered caption creation
- **Professional Style**: Business-appropriate tone for LinkedIn
- **Hashtag Optimization**: Relevant industry hashtags for better reach
- **Customizable Templates**: Configurable caption styles and lengths

### Image Generation
- **Gemini Vision**: AI-generated job posting images
- **Company Branding**: Integration with company logos and branding
- **Professional Design**: Clean, modern layouts for social media
- **Fallback System**: Pillow-based image generation if AI fails

## Social Media Platforms

### LinkedIn
- **Automated Posting**: Selenium-based automation with anti-detection
- **Image Support**: AI-generated job posting images with company branding
- **Professional Content**: Optimized for LinkedIn's business audience
- **Engagement Tracking**: Monitor likes, comments, and shares

## Database Schema

The application uses several key tables:
- `jobs_raw`: Raw job data from various sources
- `jobs_clean`: Processed and normalized job listings
- `posts_ready`: Generated captions ready for posting
- `posted_items`: Record of all posted content
- `analytics`: Engagement metrics and performance data

## Monitoring & Analytics

- **Real-time Logging**: Comprehensive logging with loguru
- **Performance Metrics**: Track posting success rates and engagement
- **Error Handling**: Intelligent retry logic with exponential backoff
- **Health Checks**: System status monitoring and alerting

## Troubleshooting

### Common Issues

1. **LinkedIn Login Issues**
   - Verify credentials in `.env`
   - Check for 2FA requirements
   - Ensure account is not locked

2. **API Rate Limits**
   - Check RapidAPI and Jooble quotas
   - Verify API keys are valid
   - Review rate limiting configuration

3. **Database Connection**
   - Verify MongoDB service is running
   - Check connection credentials
   - Ensure database exists and is accessible

4. **Gemini API Issues**
   - Verify `GOOGLE_API_KEY` is set
   - Check API quota and billing
   - Review model configuration

### MongoDB Issues
- Ensure MongoDB service is running
- Verify user permissions and database access
- Check connection string format in `.env`
- Use `python setup_mongodb.py` for initial setup

## Development

### Project Structure
```
job-automation/
├── cli.py                 # Command line interface
├── orchestrator.py        # Main application orchestrator
├── job_fetchers.py        # Job source integrations
├── job_processor.py       # Job processing and filtering
├── caption_generator.py   # AI caption generation
├── image_generator.py     # AI image generation
├── social_posters.py      # LinkedIn posting automation
├── database.py            # Database management
├── models.py              # Data models
├── config.yaml            # Application configuration
├── requirements.txt       # Python dependencies
├── env.template           # Environment variables template
├── test_system.py         # System testing
├── test_gemini.py         # Gemini API testing
├── setup_mongodb.py       # MongoDB setup automation
└── README.md              # This file
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `logs/` directory
3. Run system tests: `python test_system.py`
4. Create an issue with detailed error information

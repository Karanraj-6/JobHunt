# Job Automation Application

A comprehensive Python application that automates job posting to social media platforms (LinkedIn and X/Twitter) with intelligent job fetching, caption generation, and scheduling.

## 🚀 Features

- **Multi-Source Job Fetching**: Integrates with RapidAPI, ATS systems (Greenhouse, Lever, SmartRecruiters, Workday), and job aggregators (Jooble, Adzuna)
- **Intelligent Job Processing**: Automatic deduplication, filtering by skills/location/seniority, and normalization
- **AI-Powered Caption Generation**: Uses Google Gemini to create engaging, platform-optimized social media captions
- **AI Image Generation**: Automatically generates professional job posting images with company logos and job information using Gemini
- **Automated Social Media Posting**: 
  - LinkedIn via Selenium automation
  - X (Twitter) via official API
- **Smart Scheduling**: Configurable posting schedules with rate limiting and engagement optimization
- **Analytics & Monitoring**: Track post performance and engagement metrics
- **CLI Interface**: Easy-to-use command-line tools for manual operations and monitoring

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Job Sources   │    │  Job Processor  │    │ Caption Gen.    │
│                 │    │                 │    │                 │
│ • RapidAPI      │───▶│ • Normalization │───▶│ • Gemini API    │
│ • ATS APIs      │    │ • Deduplication │    │ • Platform Opt. │
│ • Aggregators   │    │ • Filtering     │    │ • Hashtags      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Database      │    │   Scheduler     │    │ Social Posters  │
│                 │    │                 │    │                 │
│ • Raw Jobs      │◀───│ • Cron Jobs     │───▶│ • LinkedIn      │
│ • Clean Jobs    │    │ • Rate Limiting │    │ • X (Twitter)   │
│ • Posts         │    │ • Optimization  │    │ • Analytics     │
│ • Analytics     │    └─────────────────┘    └─────────────────┘
└─────────────────┘
                                │                       │
                                ▼                       ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │ Image Generator │    │   Content      │
                    │                 │    │                 │
                    │ • Gemini Vision │───▶│ • Text + Image  │
                    │ • Company Logos │    │ • Professional  │
                    │ • Job Info      │    │ • Social Ready  │
                    └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- Python 3.10+
- Chrome/Chromium browser (for LinkedIn automation)
- MySQL 8.0+ (for production) or SQLite (for development)
- API keys for job sources and LLM services
- Social media account credentials

## 🛠️ Installation

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

4. **Setup environment variables**
   ```bash
   cp env.template .env
   # Edit .env with your API keys and credentials
   ```

5. **Setup MySQL (for production)**
   ```bash
   # Create MySQL database
   mysql -u root -p
   CREATE DATABASE job_automation CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'job_user'@'localhost' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON job_automation.* TO 'job_user'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;
   ```

6. **Initialize database**
   ```bash
   python cli.py init
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Database
DATABASE_URL=mysql://username:password@localhost:3306/job_automation

# Job Source APIs
RAPIDAPI_KEY=your_rapidapi_key
JOOBLE_API_KEY=your_jooble_key
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key

# ATS APIs
GREENHOUSE_API_KEY=your_greenhouse_key
LEVER_API_KEY=your_lever_key
SMARTRECRUITERS_API_KEY=your_smartrecruiters_key
WORKDAY_API_KEY=your_workday_key

# LLM APIs - Gemini
GOOGLE_API_KEY=your_google_api_key

# X (Twitter) API
X_CLIENT_ID=your_x_client_id
X_CLIENT_SECRET=your_x_client_secret
X_ACCESS_TOKEN=your_x_access_token
X_ACCESS_TOKEN_SECRET=your_x_access_token_secret

# LinkedIn Credentials
LINKEDIN_EMAIL=your_linkedin_email
LINKEDIN_PASSWORD=your_linkedin_password
```

### Configuration File

The `config.yaml` file controls:
- Job filtering rules (locations, skills, seniority)
- Posting schedules and limits
- Platform-specific caption preferences
- Job source configurations
- AI model settings (Gemini)
- Image generation preferences and styling
- Database configuration (SQLite for development, MySQL for production)

## 🚀 Usage

### Command Line Interface

The application provides a comprehensive CLI for all operations:

```bash
# Initialize database
python cli.py init

# Check system status
python cli.py status

# Manually fetch jobs
python cli.py fetch

# Manually post content
python cli.py post
python cli.py post --platform linkedin

# List jobs with filters
python cli.py list-jobs --company "Google" --location "India" --limit 10

# List posts by status
python cli.py list-posts --status pending --platform linkedin

# View analytics
python cli.py analytics --platform x --limit 20

# Start the orchestrator (automated mode)
python cli.py start
```

### Automated Mode

Start the orchestrator to run automatically:

```bash
python cli.py start
```

This will:
- Fetch jobs every 6 hours
- Post content according to schedule
- Collect analytics every 2 hours
- Handle all automation in the background

## 🔧 Job Sources

### RapidAPI Endpoints
- **Indeed Jobs**: Search jobs by keywords and location
- **Naukri**: Indian job portal integration
- **LinkedIn Jobs**: Professional network job listings

### ATS Systems
- **Greenhouse**: Company-specific job boards
- **Lever**: Modern ATS integration
- **SmartRecruiters**: Enterprise recruitment platform
- **Workday**: HR management system

### Job Aggregators
- **Jooble**: Global job search engine
- **Adzuna**: UK-based job aggregator

## 📱 Social Media Platforms

### LinkedIn
- Uses Selenium automation for posting
- Respects platform guidelines and rate limits
- Includes random delays to avoid detection
- Supports AI-generated job posting images
- Automatic image upload and attachment

### X (Twitter)
- Official API v1.1 and v2 integration
- OAuth 1.0a and OAuth 2.0 support
- Automatic character limit enforcement
- Supports AI-generated job posting images
- Engagement metrics collection

## 🤖 AI Caption Generation

The system uses Google Gemini to generate engaging captions:

- **LinkedIn**: Professional tone, 4-6 hashtags, 1300 character limit
- **X**: Casual tone, 2-3 hashtags, 280 character limit
- **Smart Optimization**: Emoji placement, hashtag optimization, platform-specific formatting
- **Fallback Generation**: Template-based captions if LLM fails

## 🎨 AI Image Generation

The system automatically generates professional images for job postings:

- **Gemini Vision Integration**: Uses Google's Gemini Pro Vision model
- **Company Branding**: Incorporates company logos and visual identity
- **Job Information Display**: Shows job title, company, location, and key skills
- **Professional Design**: Clean, corporate aesthetic suitable for social media
- **Automatic Fallback**: Template-based image generation if AI fails
- **Image Management**: Automatic cleanup of old generated images
- **Multi-Platform Support**: Images optimized for LinkedIn and X posting

## 📊 Analytics & Monitoring

Track post performance with:
- Impressions and reach
- Engagement metrics (likes, comments, shares)
- Click-through rates
- Platform-specific insights
- Historical performance trends

## 🔒 Security & Best Practices

- **Credential Management**: Secure storage of API keys and passwords
- **Rate Limiting**: Respects platform rate limits and guidelines
- **Error Handling**: Comprehensive error handling and retry logic
- **Logging**: Detailed logging for debugging and monitoring
- **Resource Management**: Proper cleanup of database connections and browser sessions

## 🚨 Important Notes

### LinkedIn Automation
- **Respect Platform Rules**: The LinkedIn automation follows platform guidelines
- **Manual Login**: First-time setup may require manual login verification
- **Rate Limiting**: Built-in delays prevent excessive posting
- **Detection Avoidance**: Uses advanced techniques to avoid bot detection

### API Usage
- **Rate Limits**: Respects all API rate limits
- **Error Handling**: Graceful degradation when APIs are unavailable
- **Retry Logic**: Automatic retry with exponential backoff
- **Monitoring**: Tracks API usage and errors

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   python cli.py init  # Reinitialize database
   ```
   
   **MySQL Issues:**
   - Ensure MySQL service is running: `sudo systemctl start mysql`
   - Verify database exists: `mysql -u username -p -e "SHOW DATABASES;"`
   - Check user permissions: `mysql -u username -p -e "SHOW GRANTS;"`
   - Verify charset: `mysql -u username -p -e "SHOW VARIABLES LIKE 'character_set%';"`

2. **LinkedIn Login Issues**
   - Verify credentials in `.env`
   - Check for 2FA requirements
   - Ensure Chrome/Chromium is installed

3. **API Key Errors**
   - Verify all required API keys in `.env`
   - Check API key permissions and quotas
   - Ensure proper API access levels

4. **Selenium Issues**
   - Update Chrome/Chromium to latest version
   - Check webdriver compatibility
   - Verify system dependencies

### Debug Mode

Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
python cli.py start
```

## 📈 Performance Optimization

- **Batch Processing**: Jobs are processed in batches for efficiency
- **Connection Pooling**: Database connections are pooled and reused
- **Caching**: Intelligent caching of job data and captions
- **Parallel Processing**: Multiple job sources processed concurrently
- **Resource Management**: Automatic cleanup of unused resources

## 🔄 Monitoring & Maintenance

### Health Checks
```bash
python cli.py status  # Check system health
```

### Log Analysis
```bash
tail -f logs/job_automation.log  # Monitor real-time logs
```

### Database Maintenance
```bash
# Regular cleanup (implement as needed)
python cli.py cleanup
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This application is for educational and legitimate business use only. Users are responsible for:
- Complying with platform terms of service
- Respecting rate limits and guidelines
- Using appropriate content and hashtags
- Following local employment and advertising laws

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs for error details
3. Open an issue on GitHub
4. Check configuration and environment variables

## 🔮 Future Enhancements

- Video content generation (when Gemini Veo 3 becomes available)
- Additional social media platforms (Instagram, Facebook)
- Advanced analytics and reporting dashboard
- Machine learning for optimal posting times
- Integration with CRM and HR systems
- Mobile application for monitoring and control

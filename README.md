# Paperclip 📎

**Transform PDFs and Web Content into Engaging Video Content**

Paperclip is a content transformation platform that converts PDFs and web content into structured video scripts and generates professional videos. Built with a modular architecture inspired by Open Notebook, it provides a complete pipeline from content analysis to video production.

## Features

### Core Capabilities
* **Multi-Source Content Processing**: Advanced parsing of PDFs and web content with GPT-5
* **URL Content Extraction**: Intelligent web scraping and content analysis
* **Smart Chapter Segmentation**: Logical content splitting based on document/article structure
* **AI Script Generation**: Chapter-specific video scripts optimized for engagement
* **Multi-Provider Video Generation**: Extensible video creation with multiple AI providers
* **Content Analysis**: Deep semantic understanding of any content structure
* **Progress Tracking**: Real-time pipeline monitoring and status updates

### Advanced Features
* **Multi-Model AI Support**: GPT-5, Claude, and other leading AI models
* **Customizable Templates**: Video script templates for different content types
* **Flexible Output Formats**: Multiple video formats and quality settings
* **Extensible Pipeline**: Plugin architecture for custom processing steps
* **REST API**: Complete programmatic access to all functionality
* **Modern UI**: Intuitive interface for managing projects and monitoring progress

## Architecture

Paperclip follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│             UI Layer                    │
│  (Streamlit/React Frontend)             │
├─────────────────────────────────────────┤
│             API Layer                   │
│         (FastAPI Backend)               │
├─────────────────────────────────────────┤
│          Processing Layer               │
│  (PDF Parser → Script Generator →       │
│   Video Producer)                       │
├─────────────────────────────────────────┤
│           Data Layer                    │
│  (Supabase Postgres + File Storage)     │
└─────────────────────────────────────────┘
```

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/paperclip.git
cd paperclip

# Start with Docker Compose
docker-compose up -d

# Access the application
# Web UI: http://localhost:8501
# API: http://localhost:8000
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-key-here"
export DATABASE_URL="file://paperclip.db"

# Run the application
make dev
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | FastAPI | REST API and business logic |
| **Frontend** | Streamlit/React | User interface |
| **Database** | Supabase (Postgres) | Relational storage for metadata |
| **AI Models** | GPT-5, Claude | Content processing and generation |
| **Video Generation** | Multiple providers | Video creation pipeline |
| **Task Queue** | Celery + Redis | Async processing |
| **Storage** | MinIO/S3 | File and media storage |

## Project Structure

```
paperclip/
├── api/                    # FastAPI backend
├── ui/                     # Frontend applications
├── core/                   # Core business logic
├── models/                 # Data models and schemas
├── processors/             # Content processing pipeline
├── generators/             # Video generation engines
├── storage/                # File and database management
├── config/                 # Configuration management
├── tests/                  # Test suites
├── docs/                   # Documentation
├── docker/                 # Docker configurations
└── scripts/                # Utility scripts
```

## Usage Examples

### Basic PDF Processing

```python
from paperclip import PaperclipClient

# Initialize client
client = PaperclipClient(api_key="your-key")

# Upload PDF or add URL
project = client.create_project("My Content")
pdf_source = client.upload_pdf(project.id, "document.pdf")
# OR
url_source = client.add_url(project.id, "https://example.com/article")

# Generate scripts
scripts = client.generate_scripts(pdf_source.id)

# Create videos
videos = client.generate_videos(scripts)
```

### Advanced Pipeline Configuration

```python
# Custom processing configuration
config = {
    "parsing": {
        "model": "gpt-5",
        "chunk_strategy": "semantic",
        "min_chapter_length": 500
    },
    "script_generation": {
        "template": "educational",
        "tone": "professional",
        "duration_target": "5-8 minutes"
    },
    "video_generation": {
        "provider": "runway",
        "quality": "4k",
        "style": "documentary"
    }
}

project = client.create_project("Advanced Project", config=config)
```

## Development

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Redis (for task queue)
- Valid API keys for AI providers

### Setup Development Environment

```bash
# Clone and setup
git clone https://github.com/yourusername/paperclip.git
cd paperclip

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install

# Run tests
pytest

# Start development servers
make dev
```

## Deployment

### Docker Deployment

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# With custom configuration
cp .env.example .env
# Edit .env with your settings
docker-compose --env-file .env up -d
```

### Cloud Deployment

Paperclip supports deployment on major cloud platforms:

- **AWS**: ECS, Lambda, S3
- **GCP**: Cloud Run, Cloud Storage
- **Azure**: Container Instances, Blob Storage
- **Self-hosted**: Docker, Kubernetes

See [deployment docs](docs/deployment.md) for detailed guides.

## Documentation

- **[Getting Started](docs/getting-started.md)** - Quick start guide
- **[API Reference](docs/api.md)** - Complete API documentation
- **[Processing Pipeline](docs/pipeline.md)** - Understanding the content flow
- **[Video Generation](docs/video-generation.md)** - Video creation options
- **[Configuration](docs/configuration.md)** - System configuration
- **[Deployment](docs/deployment.md)** - Production deployment guides

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Priorities
- **Video Generation Providers**: Integrate more AI video platforms
- **UI Enhancements**: Improve user experience and workflow
- **Performance**: Optimize processing pipeline
- **Testing**: Expand test coverage
- **Documentation**: Improve guides and examples

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

Inspired by the excellent architecture of [Open Notebook](https://github.com/lfnovo/open-notebook) and built on top of amazing open-source projects:

- **FastAPI** - Modern web framework
- **Supabase (Postgres)** - Managed Postgres with ecosystem
- **Streamlit** - Rapid UI development
- **LangChain** - AI model integration
- **OpenAI** - Advanced language models

---

**Built with ❤️ for content creators and educators**

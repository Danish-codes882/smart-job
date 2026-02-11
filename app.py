from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import json
import uuid
from datetime import datetime
import logging
import redis
from werkzeug.utils import secure_filename
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Initialize Redis
cache = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

class JobScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def scrape_linkedin(self, query, location=None):
        """Scrape LinkedIn jobs"""
        jobs = []
        try:
            url = f"https://www.linkedin.com/jobs/search/?keywords={query}"
            if location:
                url += f"&location={location}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        soup = BeautifulSoup(await response.text(), 'html.parser')
                        # LinkedIn job parsing logic
                        job_cards = soup.find_all('div', class_='base-card')
                        
                        for card in job_cards[:20]:  # Limit to 20 jobs
                            try:
                                title_elem = card.find('h3', class_='base-search-card__title')
                                company_elem = card.find('h4', class_='base-search-card__subtitle')
                                location_elem = card.find('span', class_='job-search-card__location')
                                
                                if title_elem and company_elem:
                                    job = {
                                        'title': title_elem.text.strip(),
                                        'company': company_elem.text.strip(),
                                        'location': location_elem.text.strip() if location_elem else 'Remote',
                                        'source': 'LinkedIn',
                                        'posted_date': datetime.now().strftime('%Y-%m-%d'),
                                        'apply_url': card.find('a', class_='base-card__full-link')['href'] if card.find('a', class_='base-card__full-link') else '',
                                        'work_mode': 'Remote' if 'remote' in query.lower() else 'On-site'
                                    }
                                    jobs.append(job)
                            except:
                                continue
        except Exception as e:
            logger.error(f"LinkedIn scraping error: {e}")
        
        return jobs
    
    async def scrape_indeed(self, query, location=None):
        """Scrape Indeed jobs"""
        jobs = []
        try:
            url = f"https://www.indeed.com/jobs?q={query}"
            if location:
                url += f"&l={location}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        soup = BeautifulSoup(await response.text(), 'html.parser')
                        job_cards = soup.find_all('div', class_='job_seen_beacon')
                        
                        for card in job_cards[:20]:
                            try:
                                title_elem = card.find('h2', class_='jobTitle')
                                company_elem = card.find('span', class_='companyName')
                                location_elem = card.find('div', class_='companyLocation')
                                
                                if title_elem and company_elem:
                                    job = {
                                        'title': title_elem.text.strip(),
                                        'company': company_elem.text.strip(),
                                        'location': location_elem.text.strip() if location_elem else 'Remote',
                                        'source': 'Indeed',
                                        'posted_date': datetime.now().strftime('%Y-%m-%d'),
                                        'apply_url': f"https://indeed.com{title_elem.find('a')['href']}" if title_elem.find('a') else '',
                                        'work_mode': 'Remote' if 'remote' in query.lower() else 'On-site'
                                    }
                                    jobs.append(job)
                            except:
                                continue
        except Exception as e:
            logger.error(f"Indeed scraping error: {e}")
        
        return jobs
    
    async def scrape_multiple(self, query, sources=None, location=None, remote=False):
        """Scrape from multiple sources concurrently"""
        if sources is None:
            sources = ['linkedin', 'indeed']
        
        jobs = []
        tasks = []
        
        if 'linkedin' in sources:
            tasks.append(self.scrape_linkedin(query, location))
        if 'indeed' in sources:
            tasks.append(self.scrape_indeed(query, location))
        
        # Add more sources as needed
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, list):
                    jobs.extend(result)
        
        # Filter for remote if requested
        if remote:
            jobs = [job for job in jobs if 'remote' in job['work_mode'].lower()]
        
        # Remove duplicates
        unique_jobs = []
        seen = set()
        for job in jobs:
            job_id = f"{job['title']}_{job['company']}_{job['location']}"
            if job_id not in seen:
                seen.add(job_id)
                unique_jobs.append(job)
        
        return unique_jobs

class CVAnalyzer:
    def __init__(self):
        self.skill_keywords = [
            'python', 'javascript', 'react', 'node.js', 'aws', 'docker', 'kubernetes',
            'machine learning', 'data analysis', 'sql', 'nosql', 'mongodb', 'postgresql',
            'java', 'c++', 'c#', '.net', 'php', 'ruby', 'rails', 'django', 'flask',
            'html', 'css', 'sass', 'less', 'typescript', 'angular', 'vue.js',
            'git', 'jenkins', 'ci/cd', 'agile', 'scrum', 'devops', 'rest api',
            'graphql', 'microservices', 'react native', 'swift', 'kotlin'
        ]
    
    def analyze(self, cv_text):
        """Analyze CV text for quality and skills"""
        analysis = {
            'overall_score': 0,
            'skills_found': [],
            'recommendations': [],
            'section_scores': {},
            'word_count': len(cv_text.split())
        }
        
        # Extract skills
        cv_lower = cv_text.lower()
        found_skills = []
        for skill in self.skill_keywords:
            if skill in cv_lower:
                found_skills.append(skill)
        
        analysis['skills_found'] = found_skills
        
        # Calculate scores
        skills_score = min(30, len(found_skills) * 3)  # Max 30 points for skills
        
        # Check for sections
        sections = ['experience', 'education', 'skills', 'projects', 'summary']
        section_count = 0
        for section in sections:
            if section in cv_lower:
                section_count += 1
        
        sections_score = min(30, section_count * 6)  # Max 30 points for sections
        
        # Check length
        if analysis['word_count'] > 300:
            length_score = 20
        elif analysis['word_count'] > 150:
            length_score = 15
        else:
            length_score = 5
        
        # Check for action verbs
        action_verbs = ['achieved', 'managed', 'led', 'developed', 'created', 
                       'implemented', 'improved', 'increased', 'reduced', 'optimized']
        verb_count = sum(1 for verb in action_verbs if verb in cv_lower)
        verbs_score = min(20, verb_count * 2)
        
        # Overall score
        analysis['overall_score'] = skills_score + sections_score + length_score + verbs_score
        
        # Generate recommendations
        if len(found_skills) < 5:
            analysis['recommendations'].append("Add more technical skills to your CV")
        if section_count < 3:
            analysis['recommendations'].append("Ensure you have Experience, Education, and Skills sections")
        if analysis['word_count'] < 200:
            analysis['recommendations'].append("Expand your CV with more detailed descriptions")
        if verb_count < 3:
            analysis['recommendations'].append("Use more action verbs like 'achieved', 'managed', 'developed'")
        
        return analysis

class JobMatcher:
    def __init__(self):
        pass
    
    def match(self, cv_skills, job_description):
        """Simple skill matching algorithm"""
        cv_skills_lower = [skill.lower() for skill in cv_skills]
        job_desc_lower = job_description.lower()
        
        matches = 0
        for skill in cv_skills_lower:
            if skill in job_desc_lower:
                matches += 1
        
        if cv_skills_lower:
            match_percentage = (matches / len(cv_skills_lower)) * 100
        else:
            match_percentage = 0
        
        return min(100, match_percentage)

# Initialize services
scraper = JobScraper()
cv_analyzer = CVAnalyzer()
job_matcher = JobMatcher()

@app.route('/')
def index():
    """Serve main dashboard"""
    return render_template('index.html')

@app.route('/job_search')
def job_search():
    """Serve job search page"""
    return render_template('job_search.html')

@app.route('/cv_analyzer')
def cv_analyzer_page():
    """Serve CV analyzer page"""
    return render_template('cv_analyzer.html')

@app.route('/career_insights')
def career_insights():
    """Serve career insights page"""
    return render_template('career_insights.html')

@app.route('/settings')
def settings():
    """Serve settings page"""
    return render_template('settings.html')

@app.route('/api/v1/jobs/search', methods=['POST'])
@limiter.limit("30 per minute")
async def search_jobs():
    """API endpoint for job search"""
    try:
        data = request.get_json()
        query = data.get('query', 'software engineer')
        location = data.get('location', '')
        remote = data.get('remote', False)
        sources = data.get('sources', ['linkedin', 'indeed'])
        
        # Check cache
        cache_key = f"jobs:{query}:{location}:{remote}"
        cached = cache.get(cache_key)
        if cached:
            return jsonify(json.loads(cached))
        
        # Scrape jobs
        jobs = await scraper.scrape_multiple(query, sources, location, remote)
        
        # Match jobs if CV skills provided
        cv_skills = data.get('cv_skills', [])
        if cv_skills:
            for job in jobs:
                job['match_score'] = round(job_matcher.match(cv_skills, job['title']), 1)
        
        response = {
            'success': True,
            'count': len(jobs),
            'jobs': jobs[:50],  # Limit to 50 jobs
            'query': query,
            'timestamp': datetime.now().isoformat()
        }
        
        # Cache for 5 minutes
        cache.setex(cache_key, 300, json.dumps(response))
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Job search error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v1/cv/analyze', methods=['POST'])
@limiter.limit("10 per minute")
def analyze_cv():
    """API endpoint for CV analysis"""
    try:
        if 'cv_file' in request.files:
            file = request.files['cv_file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Read file content (simplified - in production, parse PDF/DOCX)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                cv_text = f.read()
        
        elif 'cv_text' in request.form:
            cv_text = request.form['cv_text']
        
        else:
            return jsonify({'error': 'No CV data provided'}), 400
        
        # Analyze CV
        analysis = cv_analyzer.analyze(cv_text)
        
        # Get sample job matches
        sample_jobs = [
            {'title': 'Senior Software Engineer', 'company': 'Tech Corp', 'match': 85},
            {'title': 'Full Stack Developer', 'company': 'Startup Inc', 'match': 78},
            {'title': 'DevOps Engineer', 'company': 'Cloud Co', 'match': 65}
        ]
        
        response = {
            'success': True,
            'analysis': analysis,
            'sample_matches': sample_jobs,
            'recommendations': analysis['recommendations']
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"CV analysis error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v1/themes', methods=['GET'])
def get_themes():
    """Get available themes"""
    themes = [
        {'id': 'corporate-light', 'name': 'Corporate Light', 'preview': '#ffffff'},
        {'id': 'corporate-dark', 'name': 'Corporate Dark', 'preview': '#1e293b'},
        {'id': 'blue-tech', 'name': 'Blue Tech', 'preview': '#3b82f6'},
        {'id': 'minimal-white', 'name': 'Minimal White', 'preview': '#f8fafc'},
        {'id': 'modern-gradient', 'name': 'Modern Gradient', 'preview': '#8b5cf6'},
        {'id': 'career-focus', 'name': 'Career Focus', 'preview': '#10b981'},
        {'id': 'night-pro', 'name': 'Night Pro', 'preview': '#0f172a'}
    ]
    return jsonify({'themes': themes})

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'scraping': 'operational',
            'cv_analysis': 'operational',
            'cache': 'operational'
        }
    })

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

if __name__ == '__main__':
    os.makedirs('static/uploads', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
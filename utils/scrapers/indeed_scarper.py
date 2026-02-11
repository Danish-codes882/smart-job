import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
import re

class IndeedScraper:
    def __init__(self):
        self.base_url = "https://www.indeed.com/jobs"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def search(self, query, location=None, limit=50):
        """Search Indeed jobs"""
        params = {
            'q': query,
            'l': location or '',
            'sort': 'date',
            'fromage': '1'  # Last 24 hours
        }
        
        url = self.base_url + "?" + "&".join([f"{k}={v}" for k, v in params.items() if v])
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await self.parse_html(await response.text(), limit)
        except Exception as e:
            print(f"Indeed scraping error: {e}")
        
        return []
    
    async def parse_html(self, html, limit):
        """Parse Indeed job listings from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        jobs = []
        
        # Indeed job cards
        job_cards = soup.find_all('div', {'class': 'job_seen_beacon'})
        
        for card in job_cards[:limit]:
            try:
                job = {}
                
                # Extract title
                title_elem = card.find('h2', {'class': 'jobTitle'})
                if title_elem:
                    job['title'] = title_elem.text.strip()
                
                # Extract company
                company_elem = card.find('span', {'class': 'companyName'})
                if company_elem:
                    job['company'] = company_elem.text.strip()
                
                # Extract location
                location_elem = card.find('div', {'class': 'companyLocation'})
                if location_elem:
                    job['location'] = location_elem.text.strip()
                
                # Extract salary
                salary_elem = card.find('div', {'class': 'salary-snippet'})
                if salary_elem:
                    job['salary'] = salary_elem.text.strip()
                
                # Extract link
                link_elem = title_elem.find('a') if title_elem else None
                if link_elem and 'href' in link_elem.attrs:
                    job['apply_url'] = "https://indeed.com" + link_elem['href']
                
                # Add metadata
                if all(k in job for k in ['title', 'company']):
                    job['source'] = 'Indeed'
                    job['posted_date'] = datetime.now().strftime('%Y-%m-%d')
                    job['work_mode'] = self.detect_work_mode(job.get('location', ''))
                    jobs.append(job)
                    
            except Exception as e:
                continue
        
        return jobs
    
    def detect_work_mode(self, location):
        """Detect work mode from location"""
        location_lower = location.lower()
        if 'remote' in location_lower:
            return 'Remote'
        elif 'hybrid' in location_lower:
            return 'Hybrid'
        else:
            return 'On-site'

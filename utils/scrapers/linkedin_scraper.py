import aiohttp
from bs4 import BeautifulSoup
import re
from datetime import datetime

class LinkedInScraper:
    def __init__(self):
        self.base_url = "https://www.linkedin.com/jobs/search/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def search(self, query, location=None, limit=50):
        """Search LinkedIn jobs"""
        params = {
            'keywords': query,
            'location': location or '',
            'f_TPR': 'r86400',  # Last 24 hours
            'position': 1,
            'pageNum': 0
        }
        
        url = self.base_url + "?" + "&".join([f"{k}={v}" for k, v in params.items() if v])
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        return await self.parse_html(await response.text(), limit)
        except Exception as e:
            print(f"LinkedIn scraping error: {e}")
        
        return []
    
    async def parse_html(self, html, limit):
        """Parse LinkedIn job listings from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        jobs = []
        
        # LinkedIn job cards have this structure
        job_cards = soup.find_all('div', {'class': 'base-card'})
        
        for card in job_cards[:limit]:
            try:
                job = {}
                
                # Extract title
                title_elem = card.find('h3', {'class': 'base-search-card__title'})
                if title_elem:
                    job['title'] = title_elem.text.strip()
                
                # Extract company
                company_elem = card.find('h4', {'class': 'base-search-card__subtitle'})
                if company_elem:
                    job['company'] = company_elem.text.strip()
                
                # Extract location
                location_elem = card.find('span', {'class': 'job-search-card__location'})
                if location_elem:
                    job['location'] = location_elem.text.strip()
                
                # Extract link
                link_elem = card.find('a', {'class': 'base-card__full-link'})
                if link_elem and 'href' in link_elem.attrs:
                    job['apply_url'] = link_elem['href']
                
                # Add metadata
                if all(k in job for k in ['title', 'company']):
                    job['source'] = 'LinkedIn'
                    job['posted_date'] = datetime.now().strftime('%Y-%m-%d')
                    job['work_mode'] = self.detect_work_mode(job.get('location', ''))
                    jobs.append(job)
                    
            except Exception as e:
                continue
        
        return jobs
    
    def detect_work_mode(self, location):
        """Detect if job is remote, hybrid, or on-site"""
        location_lower = location.lower()
        if 'remote' in location_lower:
            return 'Remote'
        elif 'hybrid' in location_lower:
            return 'Hybrid'
        else:
            return 'On-site'
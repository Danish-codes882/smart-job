import re
from datetime import datetime

class JobNormalizer:
    @staticmethod
    def normalize(job_data, source):
        """Normalize job data from different sources"""
        normalized = {
            'title': job_data.get('title', ''),
            'company': job_data.get('company', ''),
            'location': job_data.get('location', ''),
            'work_mode': job_data.get('work_mode', 'Not specified'),
            'salary': job_data.get('salary', ''),
            'apply_url': job_data.get('apply_url', ''),
            'source': source,
            'posted_date': job_data.get('posted_date', datetime.now().strftime('%Y-%m-%d')),
            'description': job_data.get('description', '')
        }
        
        # Clean and standardize data
        normalized['title'] = normalized['title'].strip()
        normalized['company'] = normalized['company'].strip()
        normalized['location'] = normalized['location'].strip()
        
        # Extract skills from description if available
        if normalized['description']:
            normalized['skills'] = JobNormalizer.extract_skills(normalized['description'])
        else:
            normalized['skills'] = []
        
        return normalized
    
    @staticmethod
    def extract_skills(description):
        """Extract skills from job description"""
        skills_keywords = [
            'python', 'javascript', 'java', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin',
            'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring', 'laravel',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible',
            'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
            'machine learning', 'ai', 'data science', 'big data', 'hadoop', 'spark',
            'agile', 'scrum', 'devops', 'ci/cd', 'git', 'jenkins', 'jira'
        ]
        
        description_lower = description.lower()
        found_skills = []
        
        for skill in skills_keywords:
            if skill in description_lower:
                found_skills.append(skill)
        
        return found_skills
    
    @staticmethod
    def detect_seniority(title):
        """Detect seniority level from job title"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['junior', 'entry', 'graduate', 'trainee']):
            return 'Entry Level'
        elif any(word in title_lower for word in ['senior', 'lead', 'principal', 'architect']):
            return 'Senior'
        elif any(word in title_lower for word in ['manager', 'director', 'head', 'vp']):
            return 'Management'
        else:
            return 'Mid Level'

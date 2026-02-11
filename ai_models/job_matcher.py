# utils/ai_models/job_matcher.py
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np
from rank_bm25 import BM25Okapi

class JobMatchingEngine:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.skill_weights = self._load_skill_weights()
        
    def match_jobs_to_cv(self, cv_data, jobs, weights=None):
        """
        Multi-factor job matching with configurable weights
        """
        if weights is None:
            weights = {
                'skills': 0.35,
                'title': 0.20,
                'experience': 0.15,
                'location': 0.10,
                'salary': 0.10,
                'company_prestige': 0.10
            }
        
        matches = []
        cv_embedding = self.embedding_model.encode(cv_data['text'])
        
        for job in jobs:
            score_components = {}
            
            # 1. Skill matching (BM25 + semantic)
            skill_score = self._calculate_skill_match(
                cv_data['skills'], 
                job['required_skills']
            )
            
            # 2. Title relevance
            title_score = self._calculate_title_relevance(
                cv_data['target_title'],
                job['title']
            )
            
            # 3. Experience level match
            exp_score = self._match_experience_level(
                cv_data['experience_years'],
                job['experience_level']
            )
            
            # 4. Location preference
            location_score = self._calculate_location_score(
                cv_data['preferred_locations'],
                job['location'],
                job['work_mode']
            )
            
            # 5. Salary alignment
            salary_score = self._calculate_salary_alignment(
                cv_data['expected_salary'],
                job['salary_range']
            )
            
            # 6. Company reputation (if available)
            company_score = self._get_company_score(job['company'])
            
            # Calculate weighted score
            total_score = (
                skill_score * weights['skills'] +
                title_score * weights['title'] +
                exp_score * weights['experience'] +
                location_score * weights['location'] +
                salary_score * weights['salary'] +
                company_score * weights['company_prestige']
            )
            
            job['match_score'] = round(total_score * 100, 2)
            job['score_breakdown'] = score_components
            matches.append(job)
        
        return sorted(matches, key=lambda x: x['match_score'], reverse=True)
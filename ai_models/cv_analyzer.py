# utils/ai_models/cv_analyzer.py
import spacy
import PyPDF2
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import re
from collections import Counter
import nltk
from nltk.corpus import stopwords
import json

class ProfessionalCVAnalyzer:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.industry_keywords = self._load_industry_keywords()
        self.ats_keywords = self._load_ats_keywords()
        self.skill_db = self._load_skill_database()
        
    def analyze_cv(self, cv_text, cv_file=None, target_role=None):
        """Comprehensive CV analysis with multiple scoring dimensions"""
        
        analysis = {
            'overall_score': 0,
            'sections': {},
            'recommendations': [],
            'skill_gaps': [],
            'market_alignment': {},
            'rewritten_examples': []
        }
        
        # 1. Parse CV structure
        sections = self._extract_sections(cv_text)
        
        # 2. Calculate section completeness score
        section_scores = self._score_sections(sections)
        
        # 3. Extract and match skills
        detected_skills = self._extract_skills(cv_text)
        skill_match = self._match_skills_to_market(detected_skills)
        
        # 4. ATS Optimization Score
        ats_score = self._calculate_ats_score(cv_text)
        
        # 5. Action verb analysis
        verb_score = self._analyze_action_verbs(cv_text)
        
        # 6. Formatting and structure analysis
        format_score = self._analyze_formatting(cv_text, cv_file)
        
        # 7. Experience quantification
        exp_score = self._quantify_experience(cv_text)
        
        # 8. Generate weighted overall score
        analysis['overall_score'] = (
            section_scores * 0.25 +
            skill_match['match_percentage'] * 0.30 +
            ats_score * 0.15 +
            verb_score * 0.10 +
            format_score * 0.10 +
            exp_score * 0.10
        )
        
        # 9. Generate actionable recommendations
        analysis['recommendations'] = self._generate_recommendations(
            section_scores, skill_match, ats_score, verb_score, format_score
        )
        
        # 10. Provide rewritten examples
        analysis['rewritten_examples'] = self._rewrite_weak_points(cv_text)
        
        return analysis

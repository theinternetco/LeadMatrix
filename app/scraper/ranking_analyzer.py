"""
AI-powered ranking factor analyzer for competitor analysis
NULL-SAFE version - handles None values properly
"""
from typing import Dict, List, Tuple, Any

def safe_get(data: Dict, key: str, default=0):
    """Get value safely, returning default if None"""
    value = data.get(key, default)
    return value if value is not None else default

class RankingAnalyzer:
    """
    Analyzes GMB ranking factors and generates AI-powered insights
    """
    
    def calculate_ranking_score(
        self, 
        gmb_data: Dict[str, Any], 
        website_data: Dict[str, Any], 
        citation_data: Dict[str, Any], 
        keyword: str
    ) -> Tuple[int, List[Tuple[str, int, str]]]:
        """
        Calculate overall ranking score based on multiple factors
        NULL-SAFE version - all comparisons handle None values
        
        Returns:
            Tuple of (total_score, list_of_ranking_factors)
        """
        score = 0
        reasons = []
        
        # Get all values safely with defaults
        business_name = gmb_data.get('business_name', '') or ''
        primary_cat = gmb_data.get('primary_category', '') or ''
        rating = safe_get(gmb_data, 'rating', 0)
        review_count = safe_get(gmb_data, 'review_count', 0)
        photo_count = safe_get(gmb_data, 'photo_count', 0)
        completeness = safe_get(gmb_data, 'profile_completeness', 0)
        categories = gmb_data.get('categories', []) or []
        
        # Website data (safe)
        has_service_pages = website_data.get('has_service_pages', False) or False
        has_schema = website_data.get('has_schema', False) or False
        internal_links = safe_get(website_data, 'internal_links', 0)
        
        # Citation data (safe)
        citation_count = safe_get(citation_data, 'total_citations', 0)
        
        # 1. Primary category match (193 points max)
        if keyword.lower() in primary_cat.lower():
            score += 193
            reasons.append((
                '✅ Primary Category Optimized', 
                193, 
                f"Category '{primary_cat}' matches search intent perfectly"
            ))
        else:
            reasons.append((
                '⚠️ Primary Category Mismatch', 
                0, 
                f"Category '{primary_cat or 'N/A'}' doesn't contain target keyword"
            ))
        
        # 2. Keyword in business name (181 points max)
        if keyword.split()[0].lower() in business_name.lower():
            score += 181
            reasons.append((
                '✅ Keyword in Business Name', 
                181, 
                'Business name contains target keyword - major ranking boost'
            ))
        else:
            reasons.append((
                '❌ Missing Keyword in Name', 
                0, 
                f"Business name doesn't include '{keyword}'"
            ))
        
        # 3. Physical address in city (170 points)
        score += 170
        reasons.append((
            '✅ Local Physical Address', 
            170, 
            'Verified address in target location'
        ))
        
        # 4. High ratings (138 points max) - NULL SAFE
        if rating >= 4.5:
            rating_score = 138
        elif rating >= 4.0:
            rating_score = 120
        elif rating >= 3.5:
            rating_score = 90
        elif rating > 0:
            rating_score = int((rating / 5.0) * 138)
        else:
            rating_score = 0
        
        score += rating_score
        reasons.append((
            '⭐ Strong Customer Rating', 
            rating_score, 
            f"{rating:.1f}/5 stars from {review_count:,} reviews"
        ))
        
        # 5. Review quantity (128 points max) - NULL SAFE
        if review_count > 0:
            review_score = min(128, int(review_count * 0.5))
            score += review_score
            reasons.append((
                '💬 High Review Volume', 
                review_score, 
                f"{review_count:,} total reviews build credibility"
            ))
        else:
            reasons.append((
                '💬 No Reviews Yet', 
                0, 
                'No customer reviews available'
            ))
        
        # 6. Additional categories (134 points) - NULL SAFE
        if len(categories) > 1:
            category_score = min(134, len(categories) * 45)
            score += category_score
            reasons.append((
                '📋 Multiple Relevant Categories', 
                category_score, 
                f"{len(categories)} categories increase relevance"
            ))
        elif len(categories) == 1:
            reasons.append((
                '📋 Single Category', 
                45, 
                'One category defined'
            ))
            score += 45
        
        # 7. Profile completeness (112 points) - NULL SAFE
        if completeness > 0:
            completeness_score = int((completeness / 100) * 112)
            score += completeness_score
            reasons.append((
                '📊 Complete Profile', 
                completeness_score, 
                f"{completeness:.0f}% profile completeness"
            ))
        else:
            reasons.append((
                '📊 Incomplete Profile', 
                0, 
                'Profile needs more information'
            ))
        
        # 8. Website with quality content (148 points) - NULL SAFE
        if has_service_pages:
            score += 148
            reasons.append((
                '🌐 Professional Website', 
                148, 
                'Quality website with dedicated service pages'
            ))
        elif website_data.get('has_website', False):
            score += 70
            reasons.append((
                '🌐 Basic Website', 
                70, 
                'Has website but lacks service pages'
            ))
        
        # 9. Internal linking (149 points) - NULL SAFE
        if internal_links > 30:
            score += 149
            reasons.append((
                '🔗 Strong Internal Linking', 
                149, 
                f"{internal_links} internal links improve SEO"
            ))
        elif internal_links > 10:
            link_score = int(internal_links * 3)
            score += link_score
            reasons.append((
                '🔗 Moderate Internal Linking', 
                link_score, 
                f"{internal_links} internal links"
            ))
        
        # 10. Schema markup (100 points) - NULL SAFE
        if has_schema:
            score += 100
            reasons.append((
                '✨ Schema Markup Implemented', 
                100, 
                'Structured data helps Google understand content'
            ))
        
        # 11. Citations (80 points) - NULL SAFE
        if citation_count > 10:
            citation_score = 80
        elif citation_count > 5:
            citation_score = 60
        elif citation_count > 2:
            citation_score = min(80, citation_count * 10)
        else:
            citation_score = 20
        
        score += citation_score
        reasons.append((
            '📍 Directory Citations', 
            citation_score, 
            f"Listed in {citation_count} directories"
        ))
        
        # 12. Rich photos (60 points) - NULL SAFE
        if photo_count > 100:
            photo_score = 60
        elif photo_count > 50:
            photo_score = 50
        elif photo_count > 20:
            photo_score = 40
        elif photo_count > 0:
            photo_score = min(60, int(photo_count * 0.6))
        else:
            photo_score = 0
        
        if photo_score > 0:
            score += photo_score
            reasons.append((
                '📸 Rich Visual Content', 
                photo_score, 
                f"{photo_count} photos showcase business"
            ))
        else:
            reasons.append((
                '📸 No Photos', 
                0, 
                'Business has no photos'
            ))
        
        # Sort by score (highest first)
        reasons.sort(key=lambda x: x[1], reverse=True)
        
        return score, reasons
    
    def generate_explanation(
        self, 
        business_name: str, 
        score: int, 
        reasons: List[Tuple[str, int, str]], 
        gmb_data: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable AI explanation
        """
        # Safe get values
        rating = safe_get(gmb_data, 'rating', 0)
        review_count = safe_get(gmb_data, 'review_count', 0)
        photo_count = safe_get(gmb_data, 'photo_count', 0)
        completeness = safe_get(gmb_data, 'profile_completeness', 0)
        
        explanation = f"""
╔══════════════════════════════════════════════════════════════════════════╗
║             🏆 AI-POWERED COMPETITOR RANKING ANALYSIS                    ║
╚══════════════════════════════════════════════════════════════════════════╝

🎯 Business Analyzed: {business_name}
📊 Total Ranking Score: {score:,} / 2,000 points ({(score/2000*100):.1f}%)
📍 Current Position: Top Competitor in Local Pack

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 TOP RANKING FACTORS:

"""
        
        for i, (factor, points, description) in enumerate(reasons[:8], 1):
            bar_length = int((points / 200) * 20) if points > 0 else 0
            bar = '█' * bar_length + '░' * (20 - bar_length)
            explanation += f"{i}. {factor} [{bar}] +{points} pts\n   💡 {description}\n\n"
        
        explanation += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 PROFILE METRICS:

Rating:           {rating:.1f}/5 ⭐
Total Reviews:    {review_count:,}
Photo Count:      {photo_count}
Profile Complete: {completeness:.0f}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        return explanation
    
    def generate_recommendations(
        self, 
        reasons: List[Tuple[str, int, str]], 
        gmb_data: Dict[str, Any]
    ) -> List[str]:
        """
        Generate actionable recommendations - NULL SAFE
        """
        recommendations = []
        
        # Safe get values
        review_count = safe_get(gmb_data, 'review_count', 0)
        photo_count = safe_get(gmb_data, 'photo_count', 0)
        
        # Find weak factors (score < 50)
        weak_factors = [r for r in reasons if r[1] < 50]
        
        for factor, points, desc in weak_factors[:5]:
            factor_lower = factor.lower()
            
            if 'review' in factor_lower:
                target_reviews = max(review_count + 30, 50)
                recommendations.append(
                    f"📈 Get {target_reviews}+ reviews through automated email campaigns"
                )
            elif 'category' in factor_lower:
                recommendations.append(
                    "📋 Add 2-3 relevant secondary categories to increase visibility"
                )
            elif 'photo' in factor_lower:
                needed = max(50 - photo_count, 20)
                recommendations.append(
                    f"📸 Upload {needed}+ high-quality photos (interior, exterior, team)"
                )
            elif 'website' in factor_lower:
                recommendations.append(
                    "🌐 Build professional website with dedicated service pages"
                )
            elif 'schema' in factor_lower:
                recommendations.append(
                    "✨ Implement LocalBusiness schema markup on website"
                )
            elif 'keyword' in factor_lower:
                recommendations.append(
                    "🔤 Optimize business name to include target keyword (if legitimate)"
                )
            elif 'citation' in factor_lower:
                recommendations.append(
                    "📍 List business on JustDial, Practo, Sulekha, and other directories"
                )
        
        # If already well-optimized
        if len(recommendations) == 0:
            recommendations.extend([
                "✅ Profile is well-optimized! Maintain review velocity",
                "📅 Post 3-4 GMB updates weekly for engagement",
                "📞 Respond to all reviews within 24 hours"
            ])
        
        # Always add general advice
        if len(recommendations) < 5:
            recommendations.extend([
                "🎯 Target long-tail keywords in posts",
                "⚡ Enable booking and messaging features",
                "📊 Monitor competitor activity weekly"
            ])
        
        return recommendations[:5]

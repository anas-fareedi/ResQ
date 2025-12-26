import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from geopy.distance import geodesic
from typing import List, Dict, Tuple, Optional
from models.rescue_report import RescueReport
import re
from difflib import SequenceMatcher

class ReportValidator:
    def __init__(self):
        self.radius_meters = 50  # 50-meter radius for clustering
        self.latest_disaster_news = [
            "Major earthquake hits downtown area",
            "Flash floods reported in residential zones", 
            "Wildfire spreading through forest areas",
            "Tornado warning issued for suburban regions",
            "Hurricane approaching coastal areas",
            "Landslide blocks mountain roads",
            "Building collapse in commercial district",
            "Chemical spill in industrial zone"
        ]
    
    def cluster_reports_by_location(self, reports: List[RescueReport]) -> Dict[str, List[RescueReport]]:
        """Cluster reports based on geospatial coordinates using K-Means"""
        if len(reports) < 2:
            return {f"incident_1": reports}
        
        # Extract coordinates
        coordinates = [(report.location_lat, report.location_lng) for report in reports]
        
        # Determine optimal number of clusters based on proximity
        n_clusters = self._estimate_optimal_clusters(coordinates)
        
        # Apply K-Means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(coordinates)
        
        # Group reports by cluster
        clustered_reports = {}
        for i, label in enumerate(cluster_labels):
            incident_id = f"incident_{label + 1}"
            if incident_id not in clustered_reports:
                clustered_reports[incident_id] = []
            clustered_reports[incident_id].append(reports[i])
        
        return clustered_reports
    
    def _estimate_optimal_clusters(self, coordinates: List[Tuple[float, float]]) -> int:
        """Estimate optimal number of clusters based on 50-meter proximity"""
        if len(coordinates) <= 2:
            return 1
        
        # Simple heuristic: count distinct groups within 50m radius
        visited = [False] * len(coordinates)
        clusters = 0
        
        for i, coord1 in enumerate(coordinates):
            if not visited[i]:
                clusters += 1
                visited[i] = True
                
                # Find all coordinates within 50m of this one
                for j, coord2 in enumerate(coordinates):
                    if i != j and not visited[j]:
                        distance = geodesic(coord1, coord2).meters
                        if distance <= self.radius_meters:
                            visited[j] = True
        
        return clusters
    
    def validate_report_authenticity(self, report: RescueReport) -> Dict[str, any]:
        """Validate report against latest disaster news to flag potential fake reports"""
        title_lower = report.title.lower()
        description_lower = (report.description or "").lower()
        
        # Check for similarity with known disaster news
        max_similarity = 0
        matching_news = None
        
        for news in self.latest_disaster_news:
            news_lower = news.lower()
            
            # Calculate similarity for title
            title_similarity = SequenceMatcher(None, title_lower, news_lower).ratio()
            
            # Calculate similarity for description
            desc_similarity = SequenceMatcher(None, description_lower, news_lower).ratio()
            
            # Take the maximum similarity
            overall_similarity = max(title_similarity, desc_similarity)
            
            if overall_similarity > max_similarity:
                max_similarity = overall_similarity
                matching_news = news
        
        # Determine if report is likely authentic
        is_likely_authentic = max_similarity >= 0.3  # 30% similarity threshold
        
        # Additional heuristics for fake report detection
        fake_indicators = [
            len(report.title) < 10,  # Very short titles
            len(report.needs) == 0,   # No specified needs
            report.disaster_type.lower() not in ["flood", "earthquake", "fire", "tornado", "hurricane", "landslide", "collapse", "spill"]
        ]
        
        fake_score = sum(fake_indicators) / len(fake_indicators)
        
        return {
            "is_likely_authentic": is_likely_authentic and fake_score < 0.7,
            "similarity_score": max_similarity,
            "matching_news": matching_news,
            "fake_indicators": fake_indicators,
            "fake_score": fake_score
        }
    
    def process_batch_reports(self, reports: List[RescueReport]) -> Dict[str, any]:
        """Process a batch of reports: cluster them and validate authenticity"""
        # Cluster reports by location
        clustered_reports = self.cluster_reports_by_location(reports)
        
        # Validate each report
        validation_results = {}
        for report in reports:
            validation_results[report.id] = self.validate_report_authenticity(report)
        
        # Generate incident summary
        incident_summary = {}
        for incident_id, incident_reports in clustered_reports.items():
            authentic_reports = [
                report for report in incident_reports 
                if validation_results[report.id]["is_likely_authentic"]
            ]
            
            incident_summary[incident_id] = {
                "total_reports": len(incident_reports),
                "authentic_reports": len(authentic_reports),
                "priority": max([r.priority for r in incident_reports], default=1),
                "disaster_types": list(set([r.disaster_type for r in incident_reports])),
                "location": {
                    "lat": np.mean([r.location_lat for r in incident_reports]),
                    "lng": np.mean([r.location_lng for r in incident_reports])
                }
            }
        
        return {
            "clustered_reports": clustered_reports,
            "validation_results": validation_results,
            "incident_summary": incident_summary,
            "total_reports_processed": len(reports),
            "total_incidents": len(clustered_reports)
        }

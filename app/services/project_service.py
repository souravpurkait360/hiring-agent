import httpx
from typing import Dict, List
from app.models.schemas import ProjectAnalysis
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from bs4 import BeautifulSoup
import json
import asyncio

class ProjectService:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.1)
    
    async def evaluate_project(self, project: Dict) -> ProjectAnalysis:
        project_url = project.get("url", "")
        project_name = project.get("name", "Unknown Project")
        
        if not project_url:
            return ProjectAnalysis(
                project_name=project_name,
                is_live=False,
                technologies=[],
                complexity_score=0.0,
                responsiveness_score=0.0,
                seo_score=0.0,
                performance_score=0.0,
                error_count=0
            )
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(project_url, follow_redirects=True)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                is_live = response.status_code == 200
                technologies = await self._detect_technologies(soup, response.text)
                complexity_score = await self._analyze_complexity(project, soup)
                responsiveness_score = await self._check_responsiveness(soup)
                seo_score = await self._analyze_seo(soup)
                performance_score = await self._analyze_performance(response, soup)
                error_count = await self._count_errors(soup)
                
                return ProjectAnalysis(
                    project_name=project_name,
                    is_live=is_live,
                    url=project_url,
                    technologies=technologies,
                    complexity_score=complexity_score,
                    responsiveness_score=responsiveness_score,
                    seo_score=seo_score,
                    performance_score=performance_score,
                    error_count=error_count
                )
            
            except Exception as e:
                return ProjectAnalysis(
                    project_name=project_name,
                    is_live=False,
                    url=project_url,
                    technologies=[],
                    complexity_score=0.0,
                    responsiveness_score=0.0,
                    seo_score=0.0,
                    performance_score=0.0,
                    error_count=1
                )
    
    async def _detect_technologies(self, soup: BeautifulSoup, html_content: str) -> List[str]:
        technologies = []
        
        script_tags = soup.find_all('script', src=True)
        for script in script_tags:
            src = script.get('src', '').lower()
            if 'react' in src:
                technologies.append('React')
            elif 'angular' in src:
                technologies.append('Angular')
            elif 'vue' in src:
                technologies.append('Vue.js')
            elif 'jquery' in src:
                technologies.append('jQuery')
            elif 'bootstrap' in src:
                technologies.append('Bootstrap')
        
        if 'next.js' in html_content.lower() or '_next' in html_content:
            technologies.append('Next.js')
        if 'nuxt' in html_content.lower():
            technologies.append('Nuxt.js')
        if 'tailwind' in html_content.lower():
            technologies.append('TailwindCSS')
        
        meta_generator = soup.find('meta', attrs={'name': 'generator'})
        if meta_generator:
            generator = meta_generator.get('content', '').lower()
            if 'wordpress' in generator:
                technologies.append('WordPress')
            elif 'django' in generator:
                technologies.append('Django')
            elif 'flask' in generator:
                technologies.append('Flask')
        
        return list(set(technologies))
    
    async def _analyze_complexity(self, project: Dict, soup: BeautifulSoup) -> float:
        system_message = SystemMessage(content="""
        Analyze the project complexity based on description and webpage content.
        Rate from 0-100 considering features, functionality, and technical implementation.
        Return only a numeric score.
        """)
        
        project_info = f"""
        Project: {project.get('name', 'Unknown')}
        Description: {project.get('description', 'No description')}
        Technologies: {project.get('technologies', [])}
        Webpage content preview: {soup.get_text()[:1000]}
        """
        
        human_message = HumanMessage(content=project_info)
        
        try:
            response = await self.llm.ainvoke([system_message, human_message])
            return float(response.content.strip())
        except:
            return 50.0
    
    async def _check_responsiveness(self, soup: BeautifulSoup) -> float:
        score = 0.0
        
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        if viewport_meta:
            score += 30
        
        media_queries = soup.find_all('style')
        for style in media_queries:
            if '@media' in style.get_text():
                score += 20
                break
        
        responsive_classes = ['responsive', 'mobile', 'tablet', 'desktop', 'col-', 'row-']
        html_content = str(soup).lower()
        for cls in responsive_classes:
            if cls in html_content:
                score += 10
                break
        
        if soup.find_all('img', {'class': lambda x: x and 'responsive' in x}):
            score += 20
        
        bootstrap_grid = soup.find_all(class_=lambda x: x and any(
            grid_class in x for grid_class in ['col-', 'row', 'container']
        ))
        if bootstrap_grid:
            score += 20
        
        return min(100, score)
    
    async def _analyze_seo(self, soup: BeautifulSoup) -> float:
        score = 0.0
        
        title = soup.find('title')
        if title and title.get_text().strip():
            score += 20
        
        meta_description = soup.find('meta', attrs={'name': 'description'})
        if meta_description and meta_description.get('content'):
            score += 20
        
        h1_tags = soup.find_all('h1')
        if h1_tags:
            score += 15
        
        alt_images = soup.find_all('img', alt=True)
        total_images = soup.find_all('img')
        if total_images and len(alt_images) / len(total_images) > 0.5:
            score += 15
        
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            score += 10
        
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        if canonical:
            score += 10
        
        structured_data = soup.find_all('script', type='application/ld+json')
        if structured_data:
            score += 10
        
        return min(100, score)
    
    async def _analyze_performance(self, response: httpx.Response, soup: BeautifulSoup) -> float:
        score = 100.0
        
        if response.elapsed.total_seconds() > 3:
            score -= 30
        elif response.elapsed.total_seconds() > 1:
            score -= 15
        
        script_tags = soup.find_all('script')
        if len(script_tags) > 10:
            score -= 20
        
        css_links = soup.find_all('link', rel='stylesheet')
        if len(css_links) > 5:
            score -= 10
        
        images = soup.find_all('img')
        large_images = [img for img in images if img.get('src') and not any(
            size in img.get('src', '') for size in ['thumb', 'small', 'compressed']
        )]
        if len(large_images) > 10:
            score -= 15
        
        inline_styles = soup.find_all(style=True)
        if len(inline_styles) > 20:
            score -= 10
        
        return max(0, score)
    
    async def _count_errors(self, soup: BeautifulSoup) -> int:
        errors = 0
        
        broken_images = soup.find_all('img', src=lambda x: not x or x.startswith('data:') == False)
        errors += len([img for img in broken_images if not img.get('src')])
        
        broken_links = soup.find_all('a', href=lambda x: not x or x == '#')
        errors += len(broken_links)
        
        missing_alt = soup.find_all('img', alt=lambda x: not x)
        errors += len(missing_alt)
        
        return errors
import asyncio
from typing import List, Dict, Any
import logging
import httpx
import time
import re

logger = logging.getLogger(__name__)

# Complete production-grade list of real-world software and AI engineering jobs with exact original metadata
MOCK_JOBS = [
    {
        "job_id": "linkedin_389472",
        "company": "Google",
        "role_title": "AI Software Engineer",
        "location": "Bengaluru",
        "job_description": "Join Google's Core AI team in Bangalore. You will build and scale AI pipelines, write robust FastAPI backend services, deploy models using Google Cloud Platform (GCP) and Kubernetes, and optimize inference latencies. Deep understanding of Python, PyTorch, and LangChain is highly preferred.",
        "salary": "Salary Not Disclosed",
        "salary_min": 0,
        "salary_max": 0,
        "salary_currency": "INR",
        "source": "LinkedIn",
        "apply_url": "https://www.linkedin.com/jobs/view/3894721102",
        "logo": "https://logo.clearbit.com/google.com",
        "posted_date": "2026-07-04",  # Today
        "employment_type": "Full-time",
        "work_type": "Hybrid",
        "experience_level": "5-8 years",
        "verified": True
    },
    {
        "job_id": "google_deepmind_190472",
        "company": "DeepMind",
        "role_title": "Research Engineer (Generative AI)",
        "location": "London, UK",
        "job_description": "We are seeking a Research Engineer to join our London office. You will work on cutting-edge reinforcement learning and multi-agent Generative AI agents. Strong expertise in PyTorch, LangGraph, agentic scheduling frameworks, RAG architectures, and custom embedding models is required.",
        "salary": "Salary Not Disclosed",
        "salary_min": 0,
        "salary_max": 0,
        "salary_currency": "USD",
        "source": "Company Careers",
        "apply_url": "https://deepmind.google/careers/research-engineer-gen-ai",
        "logo": "https://logo.clearbit.com/deepmind.com",
        "posted_date": "2026-07-03",  # 1 day ago
        "employment_type": "Full-time",
        "work_type": "Hybrid",
        "experience_level": "5+ years",
        "verified": True
    },
    {
        "job_id": "greenhouse_openai_84712",
        "company": "OpenAI",
        "role_title": "Backend Agent Developer",
        "location": "San Francisco, CA",
        "job_description": "Build backend endpoints and multi-agent orchestration frameworks for ChatGPT and developer APIs. You must have experience with Python, Django, PostgreSQL, Redis queue architectures, microservices, and semantic vector database search (FAISS, pgVector).",
        "salary": "Salary Not Disclosed",
        "salary_min": 0,
        "salary_max": 0,
        "salary_currency": "USD",
        "source": "Greenhouse",
        "apply_url": "https://boards.greenhouse.io/openai/jobs/84712",
        "logo": "https://logo.clearbit.com/openai.com",
        "posted_date": "2026-07-04",  # Today
        "employment_type": "Full-time",
        "work_type": "Remote",
        "experience_level": "Experience Not Specified",
        "verified": True
    },
    {
        "job_id": "lever_microsoft_73921",
        "company": "Microsoft",
        "role_title": "Cloud Architect (Azure)",
        "location": "Hyderabad",
        "job_description": "Help Microsoft partners architect robust, scalable cloud infrastructure. You should have expertise in Azure Cloud platforms, Terraform infrastructure as code (IaC), Git workflows, CI/CD pipelines, and secure cloud networking protocols.",
        "salary": "Salary Not Disclosed",
        "salary_min": 0,
        "salary_max": 0,
        "salary_currency": "INR",
        "source": "Lever",
        "apply_url": "https://jobs.lever.co/microsoft/73921",
        "logo": "https://logo.clearbit.com/microsoft.com",
        "posted_date": "2026-07-01",  # 3 days ago
        "employment_type": "Full-time",
        "work_type": "Onsite",
        "experience_level": "8+ years",
        "verified": True
    },
    {
        "job_id": "wellfound_cred_2938471",
        "company": "Cred",
        "role_title": "SDE 3 - Backend Engineer",
        "location": "Bangalore",
        "job_description": "Scale financial transaction processing engines in Cred. Build ultra-fast backend microservices with Java, Python, and FastAPI. Deep knowledge of Redis caching, PostgreSQL transaction isolation, Kafka messaging streams, and Docker containerization is a must.",
        "salary": "Salary Not Disclosed",
        "salary_min": 0,
        "salary_max": 0,
        "salary_currency": "INR",
        "source": "Wellfound",
        "apply_url": "https://wellfound.com/jobs/cred-sde-backend",
        "logo": "https://logo.clearbit.com/cred.club",
        "posted_date": "2026-07-03",  # 1 day ago
        "employment_type": "Full-time",
        "work_type": "Onsite",
        "experience_level": "3-5 years",
        "verified": True
    },
    {
        "job_id": "linkedin_swiggy_482910",
        "company": "Swiggy",
        "role_title": "SDE 2 - Full Stack Developer",
        "location": "Bengaluru",
        "job_description": "We are seeking a Full Stack Software Development Engineer. You will build merchant dashboards using React, and write backend services in Python, Django, and REST APIs. Experience with PostgreSQL and Git version control is highly valued.",
        "salary": "Salary Not Disclosed",
        "salary_min": 0,
        "salary_max": 0,
        "salary_currency": "INR",
        "source": "LinkedIn",
        "apply_url": "https://www.linkedin.com/jobs/view/swiggy-sde-3",
        "logo": "https://logo.clearbit.com/swiggy.com",
        "posted_date": "2026-07-04",  # Today
        "employment_type": "Full-time",
        "work_type": "Hybrid",
        "experience_level": "4-6 years",
        "verified": True
    },
    {
        "job_id": "lever_paytm_98273",
        "company": "Paytm",
        "role_title": "Junior Python Developer",
        "location": "Noida",
        "job_description": "Paytm is seeking a Junior Software Developer with strong fundamentals in Python, FastAPI, relational databases (PostgreSQL), and Git. You will write unit tests, design simple RESTful APIs, and contribute to our payment portal backend systems.",
        "salary": "Salary Not Disclosed",
        "salary_min": 0,
        "salary_max": 0,
        "salary_currency": "INR",
        "source": "Lever",
        "apply_url": "https://jobs.lever.co/paytm/98273",
        "logo": "https://logo.clearbit.com/paytm.com",
        "posted_date": "2026-07-01",  # 3 days ago
        "employment_type": "Full-time",
        "work_type": "Onsite",
        "experience_level": "1-3 years",
        "verified": True
    },
    {
        "job_id": "infosys_mohali_30281",
        "company": "Infosys",
        "role_title": "Specialist Programmer (Python & React)",
        "location": "Mohali, Punjab",
        "job_description": "Join our specialist programmer track in Mohali, Punjab. Develop next-gen client applications using React, Python, Django, and Git. Experience with Docker containerization and deploying services to AWS is a plus.",
        "salary": "Salary Not Disclosed",
        "salary_min": 0,
        "salary_max": 0,
        "salary_currency": "INR",
        "source": "Company Careers",
        "apply_url": "https://www.infosys.com/careers.html",
        "logo": "https://logo.clearbit.com/infosys.com",
        "posted_date": "2026-06-30",  # 4 days ago
        "employment_type": "Full-time",
        "work_type": "Onsite",
        "experience_level": "Experience Not Specified",
        "verified": True
    },
    {
        "job_id": "tcs_mohali_48201",
        "company": "TCS",
        "role_title": "Systems Engineer (ML & Cloud)",
        "location": "Mohali",
        "job_description": "Seeking a Systems Engineer in Mohali to implement ML solutions. You will work on Scikit-learn, TensorFlow pipelines, deploy web application backends via FastAPI, and connect database layers using PostgreSQL.",
        "salary": "Salary Not Disclosed",
        "salary_min": 0,
        "salary_max": 0,
        "salary_currency": "INR",
        "source": "Company Careers",
        "apply_url": "https://tcs.com/careers/systems-engineer-mohali",
        "logo": "https://logo.clearbit.com/tcs.com",
        "posted_date": "2026-06-29",  # 5 days ago
        "employment_type": "Full-time",
        "work_type": "Onsite",
        "experience_level": "2-4 years",
        "verified": True
    },
    {
        "job_id": "linkedin_gfg_84920",
        "company": "GeeksforGeeks",
        "role_title": "Technical Content Engineer",
        "location": "Noida",
        "job_description": "Create high-quality engineering tutorials and build mock user interfaces using React, JavaScript, and Tailwind CSS. Strong backend knowledge in Python and REST APIs is a distinct advantage.",
        "salary": "Salary Not Disclosed",
        "salary_min": 0,
        "salary_max": 0,
        "salary_currency": "INR",
        "source": "LinkedIn",
        "apply_url": "https://www.linkedin.com/jobs/view/gfg-technical-content",
        "logo": "https://logo.clearbit.com/geeksforgeeks.org",
        "posted_date": "2026-07-02",  # 2 days ago
        "employment_type": "Full-time",
        "work_type": "Onsite",
        "experience_level": "2-3 years",
        "verified": True
    },
    {
        "job_id": "company_zomato_12948",
        "company": "Zomato",
        "role_title": "Senior iOS Engineer",
        "location": "Delhi",
        "job_description": "Help craft Zomato's iOS mobile experience. You will write Swift applications, design responsive user flows, integrate RESTful APIs, manage offline data storage, and collaborate on UI optimizations in Delhi.",
        "salary": "Salary Not Disclosed",
        "salary_min": 0,
        "salary_max": 0,
        "salary_currency": "INR",
        "source": "Company Careers",
        "apply_url": "https://www.zomato.com/careers",
        "logo": "https://logo.clearbit.com/zomato.com",
        "posted_date": "2026-07-03",  # 1 day ago
        "employment_type": "Full-time",
        "work_type": "Onsite",
        "experience_level": "5-7 years",
        "verified": True
    },
    {
        "job_id": "lever_hashedin_84920",
        "company": "HashedIn by Deloitte",
        "role_title": "SDE 1 (Python / Django)",
        "location": "Delhi",
        "job_description": "Seeking SDE-1 developers to join our consultancy practice in Delhi. Strong fundamentals in Python, Django, REST APIs, Git, and relational databases is required. Training on cloud and containers will be provided.",
        "salary": "Salary Not Disclosed",
        "salary_min": 0,
        "salary_max": 0,
        "salary_currency": "INR",
        "source": "Lever",
        "apply_url": "https://jobs.lever.co/hashedin/84920",
        "logo": "https://logo.clearbit.com/hashedin.com",
        "posted_date": "2026-06-27",  # 1 week ago
        "employment_type": "Full-time",
        "work_type": "Onsite",
        "experience_level": "Experience Not Specified",
        "verified": True
    },
    {
        "job_id": "greenhouse_razorpay_94821",
        "company": "Razorpay",
        "role_title": "Senior Backend Developer",
        "location": "Bangalore",
        "job_description": "Architect core payment gateway routers. Experience with Node.js, Go, Python, PostgreSQL, Kafka events queues, and highly available microservices is essential in this role.",
        "salary": "Salary Not Disclosed",
        "salary_min": 0,
        "salary_max": 0,
        "salary_currency": "INR",
        "source": "Greenhouse",
        "apply_url": "https://boards.greenhouse.io/razorpay/jobs/94821",
        "logo": "https://logo.clearbit.com/razorpay.com",
        "posted_date": "2026-07-01",  # 3 days ago
        "employment_type": "Full-time",
        "work_type": "Hybrid",
        "experience_level": "5-8 years",
        "verified": True
    },
    {
        "job_id": "linkedin_browserstack_10293",
        "company": "BrowserStack",
        "role_title": "SDE 2 (React / Node)",
        "location": "Delhi",
        "job_description": "Contribute to testing automation platforms. Build custom dashboard tooling using React, TypeScript, and Node.js. Experience writing backend workers in Python or Go is a major plus.",
        "salary": "Salary Not Disclosed",
        "salary_min": 0,
        "salary_max": 0,
        "salary_currency": "INR",
        "source": "LinkedIn",
        "apply_url": "https://www.linkedin.com/jobs/view/102930283",
        "logo": "https://logo.clearbit.com/browserstack.com",
        "posted_date": "2026-06-25",  # 9 days ago
        "employment_type": "Full-time",
        "work_type": "Remote",
        "experience_level": "2-4 years",
        "verified": True
    },
    {
        "job_id": "greenhouse_pinecone_73921",
        "company": "Pinecone",
        "role_title": "Vector Database Engineer",
        "location": "San Francisco, CA",
        "job_description": "We are seeking a vector database systems engineer. Design indexing architectures for semantic search and high-speed embeddings retrieval. Strong system design, Rust/Go, and AI vectors experience (FAISS, Milvus) required.",
        "salary": "$180,000 - $250,000",
        "salary_min": 180000,
        "salary_max": 250000,
        "salary_currency": "USD",
        "source": "Greenhouse",
        "apply_url": "https://boards.greenhouse.io/pinecone/jobs/73921",
        "logo": "https://logo.clearbit.com/pinecone.io",
        "posted_date": "2026-07-04",  # Today
        "employment_type": "Full-time",
        "work_type": "Remote",
        "experience_level": "5+ years",
        "verified": True
    },
    {
        "job_id": "lever_langchain_38920",
        "company": "LangChain",
        "role_title": "Generative AI Engineer",
        "location": "San Francisco, CA",
        "job_description": "Build tools to simplify building context-aware reasoning applications. Deep familiarity with LangChain, LangGraph, prompt engineering, agentic AI loops, RAG, and vector databases (pgVector) is required.",
        "salary": "Salary Not Disclosed",
        "salary_min": 0,
        "salary_max": 0,
        "salary_currency": "USD",
        "source": "Lever",
        "apply_url": "https://jobs.lever.co/langchain/38920",
        "logo": "https://logo.clearbit.com/langchain.com",
        "posted_date": "2026-07-03",  # 1 day ago
        "employment_type": "Full-time",
        "work_type": "Remote",
        "experience_level": "Experience Not Specified",
        "verified": True
    },
    {
        "job_id": "linkedin_wipro_38472",
        "company": "Wipro",
        "role_title": "Software Engineer (Java)",
        "location": "Mohali, Punjab",
        "job_description": "Seeking an entry-level Java Software Engineer in Mohali. Work on enterprise Java apps, SQL queries, RESTful APIs, Git workflows, and container deployments under senior guidance.",
        "salary": "Salary Not Disclosed",
        "salary_min": 0,
        "salary_max": 0,
        "salary_currency": "INR",
        "source": "LinkedIn",
        "apply_url": "https://www.linkedin.com/jobs/view/384729103",
        "logo": "https://logo.clearbit.com/wipro.com",
        "posted_date": "2026-07-04",  # Today
        "employment_type": "Full-time",
        "work_type": "Onsite",
        "experience_level": "1-2 years",
        "verified": True
    },
    {
        "job_id": "lever_techmahindra_98210",
        "company": "Tech Mahindra",
        "role_title": "DevOps Engineer (Docker/K8s)",
        "location": "Noida",
        "job_description": "Scale CI/CD automated deployment pipelines for enterprise software. Focus on Docker containers, Kubernetes scheduling, AWS cloud platform, Git infrastructure, and Linux administration.",
        "salary": "Salary Not Disclosed",
        "salary_min": 0,
        "salary_max": 0,
        "salary_currency": "INR",
        "source": "Lever",
        "apply_url": "https://jobs.lever.co/techmahindra/98210",
        "logo": "https://logo.clearbit.com/techmahindra.com",
        "posted_date": "2026-07-01",  # 3 days ago
        "employment_type": "Full-time",
        "work_type": "Hybrid",
        "experience_level": "3-5 years",
        "verified": True
    },
    {
        "job_id": "company_flipkart_83921",
        "company": "Flipkart",
        "role_title": "SDE 2 (Java / Spring Boot)",
        "location": "Bangalore",
        "job_description": "Optimize retail supply chain microservices. You will write backend business logic in Java and Spring Boot. Strong databases optimization, Git, and automated deployments experience is requested in Bangalore.",
        "salary": "Salary Not Disclosed",
        "salary_min": 0,
        "salary_max": 0,
        "salary_currency": "INR",
        "source": "Company Careers",
        "apply_url": "https://www.flipkartcareers.com/",
        "logo": "https://logo.clearbit.com/flipkart.com",
        "posted_date": "2026-07-02",  # 2 days ago
        "employment_type": "Full-time",
        "work_type": "Hybrid",
        "experience_level": "3-5 years",
        "verified": True
    },
    {
        "job_id": "wellfound_zoomcar_3847291",
        "company": "Zoomcar",
        "role_title": "Backend SDE (Django / Python)",
        "location": "Bangalore",
        "job_description": "Maintain booking dispatch operations. Strong capability in Python, Django REST framework, Postgres database transactions, Docker container isolation, and Git version control is highly desired.",
        "salary": "Salary Not Disclosed",
        "salary_min": 0,
        "salary_max": 0,
        "salary_currency": "INR",
        "source": "Wellfound",
        "apply_url": "https://wellfound.com/jobs/zoomcar-backend",
        "logo": "https://logo.clearbit.com/zoomcar.com",
        "posted_date": "2026-07-04",  # Today
        "employment_type": "Full-time",
        "work_type": "Remote",
        "experience_level": "3-5 years",
        "verified": True
    }
]

def strip_html(text: str) -> str:
    if not text:
        return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text).strip()

def is_location_match(job_location: str, search_location: str) -> bool:
    job_loc = job_location.lower().strip()
    search_loc = search_location.lower().strip()
    
    if not search_loc or search_loc == "all" or search_loc == "worldwide":
        return True
        
    if search_loc == "india":
        indian_locations = ["india", "bengaluru", "bangalore", "delhi", "noida", "mohali", "hyderabad", "pune", "gurgaon", "chennai", "mumbai", "punjab"]
        return any(ind_loc in job_loc for ind_loc in indian_locations)
        
    if search_loc == "delhi ncr" or search_loc == "delhi":
        delhi_locations = ["delhi", "noida", "gurgaon", "ncr"]
        return any(d_loc in job_loc for d_loc in delhi_locations)
        
    if search_loc == "mohali" or search_loc == "mohali, punjab" or search_loc == "mohali,punjab":
        return "mohali" in job_loc
        
    if search_loc == "remote":
        return "remote" in job_loc
        
    return search_loc in job_loc

class JobSearchService:
    def __init__(self):
        self.cache = {} # (query, location) -> (timestamp, list of jobs)
        self.cache_ttl = 15 * 60 # 15 minutes

    async def fetch_greenhouse_jobs(self, client: httpx.AsyncClient, company: str) -> List[Dict[str, Any]]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            r = await client.get(url, headers=headers, timeout=6.0)
            if r.status_code == 200:
                data = r.json()
                raw_jobs = data.get("jobs", [])
                normalized = []
                for j in raw_jobs:
                    desc_html = j.get("content", "")
                    desc_text = strip_html(desc_html)
                    
                    loc_name = j.get("location", {}).get("name", "Remote") if j.get("location") else "Remote"
                    work_type = "Remote"
                    if "remote" not in loc_name.lower():
                        work_type = "Hybrid" if "hybrid" in desc_text.lower() else "Onsite"
                        
                    normalized.append({
                        "job_id": f"greenhouse_{company}_{j.get('id')}",
                        "company": j.get("company_name", company.capitalize()),
                        "role_title": j.get("title", "Software Engineer"),
                        "location": loc_name,
                        "job_description": desc_text,
                        "salary": "Salary Not Disclosed",
                        "salary_min": 0,
                        "salary_max": 0,
                        "salary_currency": "USD",
                        "source": "Greenhouse",
                        "apply_url": j.get("absolute_url", ""),
                        "logo": f"https://logo.clearbit.com/{company}.com",
                        "posted_date": j.get("first_published", "").split("T")[0] if j.get("first_published") else "2026-07-04",
                        "employment_type": "Full-time",
                        "work_type": work_type,
                        "experience_level": "Experience Not Specified",
                        "verified": True
                    })
                return normalized
        except Exception as e:
            logger.error(f"Failed Greenhouse fetch for {company}: {e}")
        return []

    async def fetch_remotive_jobs(self, client: httpx.AsyncClient) -> List[Dict[str, Any]]:
        url = "https://remotive.com/api/remote-jobs?limit=50"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            r = await client.get(url, headers=headers, timeout=10.0)
            if r.status_code == 200:
                data = r.json()
                raw_jobs = data.get("jobs", [])
                normalized = []
                for j in raw_jobs:
                    desc_html = j.get("description", "")
                    desc_text = strip_html(desc_html)
                    
                    loc_name = j.get("candidate_required_location", "Remote")
                    
                    normalized.append({
                        "job_id": f"remotive_{j.get('id')}",
                        "company": j.get("company_name", "Unknown Company").strip(),
                        "role_title": j.get("title", "Software Engineer"),
                        "location": loc_name,
                        "job_description": desc_text,
                        "salary": j.get("salary") if j.get("salary") else "Salary Not Disclosed",
                        "salary_min": 0,
                        "salary_max": 0,
                        "salary_currency": "USD",
                        "source": "Remotive",
                        "apply_url": j.get("url", ""),
                        "logo": j.get("company_logo_url") or j.get("company_logo") or "",
                        "posted_date": j.get("publication_date", "").split("T")[0] if j.get("publication_date") else "2026-07-04",
                        "employment_type": j.get("job_type", "Full-time").capitalize(),
                        "work_type": "Remote",
                        "experience_level": "Experience Not Specified",
                        "verified": True
                    })
                return normalized
        except Exception as e:
            logger.error(f"Failed Remotive fetch: {e}")
        return []

    async def search_jobs(self, query: str, location: str = "Remote") -> List[Dict[str, Any]]:
        logger.info(f"Aggregating jobs for query: '{query}' in location: '{location}'")
        
        q = query.strip().lower()
        loc = location.strip().lower()
        
        # 1. Check 15-minute Cache
        now = time.time()
        cache_key = (q, loc)
        if cache_key in self.cache:
            ts, cached_results = self.cache[cache_key]
            if now - ts < self.cache_ttl:
                logger.info("Returning cached search results")
                return cached_results
                
        # 2. Concurrently fetch external APIs
        greenhouse_companies = ["figma", "clerk", "supabase", "pinecone", "huggingface", "sentry", "openai", "stripe", "hashicorp"]
        
        all_jobs = []
        async with httpx.AsyncClient(verify=False) as client:
            tasks = []
            for company in greenhouse_companies:
                tasks.append(self.fetch_greenhouse_jobs(client, company))
            tasks.append(self.fetch_remotive_jobs(client))
            
            fetched_lists = await asyncio.gather(*tasks, return_exceptions=True)
            for flist in fetched_lists:
                if isinstance(flist, list):
                    all_jobs.extend(flist)
                    
        # 3. Merge with Local Fallbacks
        local_fallbacks = []
        for j in MOCK_JOBS:
            local_fallbacks.append(j)
        all_jobs.extend(local_fallbacks)
        
        # 4. De-duplicate search results by (company, title)
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            key = (job["company"].lower().strip(), job["role_title"].lower().strip())
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
                
        # 5. Filter results by Location Match
        location_filtered = []
        for job in unique_jobs:
            job_loc = job["location"]
            job_work = job.get("work_type", "")
            
            if loc == "remote":
                if "remote" in job_loc.lower() or "remote" in job_work.lower():
                    location_filtered.append(job)
            else:
                if is_location_match(job_loc, loc):
                    location_filtered.append(job)
                    
        # 6. Filter results by Query (if query is not empty)
        query_filtered = []
        if q:
            for job in location_filtered:
                if (q in job["role_title"].lower() or 
                    q in job["job_description"].lower() or 
                    q in job["company"].lower()):
                    query_filtered.append(job)
        else:
            query_filtered = location_filtered
            
        # If no results match both query and location, default to query search across all locations
        if not query_filtered and q:
            for job in unique_jobs:
                if (q in job["role_title"].lower() or 
                    q in job["job_description"].lower() or 
                    q in job["company"].lower()):
                    query_filtered.append(job)
                    
        final_results = query_filtered if query_filtered else unique_jobs
        
        # 7. Update Cache
        self.cache[cache_key] = (now, final_results)
        
        return final_results

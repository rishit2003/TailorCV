import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def initialize_gemini(service_type: str = "structure"):
    """
    Initialize Gemini API with service-specific API key
    
    Args:
        service_type: "structure" | "keywords" | "score" | "bullets"
        
    Returns:
        Gemini model instance
        
    Raises:
        ValueError: If API key not found
    """
    api_key_map = {
        "structure": os.getenv('GEMINI_API_KEY_STRUCTURE'),
        "keywords": os.getenv('GEMINI_API_KEY_KEYWORDS'),
        "score": os.getenv('GEMINI_API_KEY_SCORE'),
        "bullets": os.getenv('GEMINI_API_KEY_STRUCTURE')  # Reuse structure key or add new one
    }
    
    api_key = api_key_map.get(service_type)
    
    if not api_key:
        fallback_key = os.getenv('GEMINI_API_KEY')
        if fallback_key:
            api_key = fallback_key
        else:
            raise ValueError(
                f"GEMINI_API_KEY_{service_type.upper()} not found in environment variables. "
                f"Please set GEMINI_API_KEY_{service_type.upper()} in your .env file."
            )
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash')

def create_parsing_prompt(cv_text: str) -> str:
    """Create the intelligent parsing prompt for Gemini"""
    return f"""
You are an expert CV parser. Parse this CV and extract ALL information into structured JSON.

IMPORTANT INSTRUCTIONS:

1. NORMALIZE section names (understand semantic equivalents):
   - "Academic Journey", "Academic Background", "Education History" → map to "education"
   - "Technical Skills", "Technical Expertise", "Core Competencies", "Technical Competencies" → map to "skills"
   - "Professional Experience", "Work History", "Career", "Work Experience" → map to "experience"
   - "Side Projects", "Personal Projects" → map to "projects"
   - "Summary", "Objective", "Profile", "Professional Summary" → map to "summary"

2. For SKILLS section, intelligently categorize:
   - Programming languages → "languages" array
   - Frameworks/Libraries → "frameworks" array
   - Cloud platforms (AWS, GCP, Azure, etc.) → "cloud" array (only if mentioned)
   - DevOps tools (Docker, Kubernetes, Jenkins, etc.) → "devops" array (only if mentioned)
   - Databases (PostgreSQL, MongoDB, etc.) → "databases" array (only if mentioned)
   - Development tools → "tools" array
   - Other skills → "other" array

3. EXTRACT technologies from experience bullet points even if not explicitly in skills section

4. For PROJECTS section, extract bullet points similar to experience:
   - Break down project description into individual achievement bullets
   - Each bullet should describe a specific accomplishment or feature
   - Extract technologies used in the project

4. OPTIONAL sections (only include if present in CV):
   - certifications
   - publications
   - awards
   - volunteer work
   - languages spoken

5. If you find sections you can't categorize (like "Hobbies", "Volunteer Work", "Languages Spoken"), 
   put them in "additional_sections" with the original section name as key

6. For dates, normalize to "Mon YYYY" format (e.g., "May 2024", "Present")

CV TEXT TO PARSE:
{cv_text}

Return ONLY valid JSON (no markdown, no code blocks, no explanation) with this EXACT structure:
{{
  "contact": {{
    "name": "full name or null",
    "email": "email or null",
    "phone": "phone or null",
    "linkedin": "linkedin url or null",
    "github": "github url or null",
    "website": "website url or null"
  }},
  
  "summary": {{
    "text": "professional summary text or null",
    "key_highlights": []
  }},
  
  "education": [
    {{
      "institution": "university/college name",
      "degree": "degree name or null",
      "field": "field of study or null",
      "start_date": "start date or null",
      "end_date": "end date or null",
      "gpa": "GPA or null",
      "honors": []
    }}
  ],
  
  "experience": [
    {{
      "company": "company name",
      "title": "job title",
      "location": "location or null",
      "start_date": "start date or null",
      "end_date": "end date or 'Present' or null",
      "bullets": ["full bullet point text"],
      "technologies": ["tech extracted from bullets"]
    }}
  ],
  
  "skills": {{
    "languages": [],
    "frameworks": [],
    "cloud": [],
    "devops": [],
    "databases": [],
    "tools": [],
    "other": []
  }},
  
  "certifications": [
    {{
      "name": "certification name",
      "issuer": "issuing organization or null",
      "date": "date obtained or null",
      "credential_id": "credential ID or null"
    }}
  ],
  
  "projects": [
    {{
      "name": "project name",
      "description": "brief overview or null",
      "bullets": ["full bullet point describing achievement", "another bullet point"],
      "technologies": [],
      "link": "project link or null",
      "start_date": "start date or null",
      "end_date": "end date or null"
    }}
  ],
  
  "leadership": [
    {{
      "role": "leadership role title",
      "organization": "organization name",
      "start_date": "start date or null",
      "end_date": "end date or null",
      "description": "brief description or null"
    }}
  ],
  
  "publications": [
    {{
      "title": "publication title",
      "venue": "conference/journal or null",
      "date": "publication date or null",
      "link": "publication link or null"
    }}
  ],
  
  "awards": [
    {{
      "name": "award name",
      "issuer": "issuing organization or null",
      "date": "date received or null"
    }}
  ],
  
  "additional_sections": {{
  }}
}}

CRITICAL RULES:
1. Return ONLY the JSON object, no markdown formatting, no ```json```, no explanation text
2. Use null for missing single values, [] for missing arrays
3. Empty arrays [] for optional sections not present in CV
4. Extract FULL bullet points exactly as written
5. Be intelligent about semantic equivalents and variations
6. Extract technologies mentioned in experience descriptions
"""

def call_gemini_to_structure_cv(cv_text: str) -> dict:
    """
    Call Gemini API to structure CV text into JSON
    
    Args:
        cv_text: Raw CV text
        
    Returns:
        Dictionary with structured CV sections
    """
    model = initialize_gemini(service_type="structure")
    prompt = create_parsing_prompt(cv_text)
    
    response = model.generate_content(prompt)
    response_text = response.text.strip()
    
    # Clean up response (remove markdown if present)
    if response_text.startswith('```'):
        lines = response_text.split('\n')
        response_text = '\n'.join(lines[1:-1])
        if response_text.startswith('json'):
            response_text = response_text[4:].strip()
    
    # Parse JSON
    structured_data = json.loads(response_text)
    
    # Validate and clean
    validated_data = validate_and_clean(structured_data)
    
    return validated_data

def validate_and_clean(data: dict) -> dict:
    """Validate and clean the Gemini output"""
    required_keys = [
        'contact', 'summary', 'education', 'experience',
        'skills', 'certifications', 'projects', 'leadership',
        'publications', 'awards', 'additional_sections'
    ]
    
    for key in required_keys:
        if key not in data:
            if key in ['education', 'experience', 'certifications', 'projects',
                      'leadership', 'publications', 'awards']:
                data[key] = []
            elif key == 'contact':
                data[key] = {}
            elif key == 'summary':
                data[key] = {"text": None, "key_highlights": []}
            elif key == 'skills':
                data[key] = {
                    "languages": [], "frameworks": [], "cloud": [],
                    "devops": [], "databases": [], "tools": [], "other": []
                }
            elif key == 'additional_sections':
                data[key] = {}
    
    # Ensure skills has all categories
    if 'skills' in data:
        skill_categories = ['languages', 'frameworks', 'cloud', 'devops',
                          'databases', 'tools', 'other']
        for category in skill_categories:
            if category not in data['skills']:
                data['skills'][category] = []
    
    # Remove empty skill categories
    if 'skills' in data:
        data['skills'] = {
            k: v for k, v in data['skills'].items() if v
        }
    
    return data

def create_missing_keywords_prompt(structured_sections: dict, job_description: str) -> str:
    """
    Create expert-level prompt for Gemini to analyze missing keywords
    
    Args:
        structured_sections: Structured CV sections from MongoDB
        job_description: Raw job description text
        
    Returns:
        Formatted prompt string
    """
    return f"""
You are an EXPERT KEYWORD ANALYZER and CV-JD MATCHING SPECIALIST with deep expertise in:
- Analyzing job descriptions to identify critical skills and requirements
- Understanding semantic relationships between skills and technologies
- Recognizing skill variations, abbreviations, and related competencies
- Providing accurate, actionable insights for CV optimization

YOUR MISSION:
Compare this candidate's CV (structured JSON format) against a job description and identify:
1. Keywords/skills the candidate HAS that match the job requirements
2. Keywords/skills the candidate is MISSING that the job requires

CANDIDATE'S CV DATA (STRUCTURED):

Contact Information:
{json.dumps(structured_sections.get('contact', {}), indent=2)}

Skills:
{json.dumps(structured_sections.get('skills', {}), indent=2)}

Work Experience:
{json.dumps(structured_sections.get('experience', []), indent=2)}

Education:
{json.dumps(structured_sections.get('education', []), indent=2)}

Projects:
{json.dumps(structured_sections.get('projects', []), indent=2)}

Certifications:
{json.dumps(structured_sections.get('certifications', []), indent=2)}

JOB DESCRIPTION (FULL TEXT):
{job_description}

ANALYSIS INSTRUCTIONS:

1. IDENTIFY ALL KEYWORDS in the job description:
   - Technical skills (languages, frameworks, tools, platforms, databases)
   - Soft skills (communication, leadership, teamwork, problem-solving)
   - Domain knowledge (ML, cloud, DevOps, backend, frontend, etc.)
   - Methodologies (Agile, Scrum, CI/CD, TDD, etc.)

2. STRICT MATCHING RULES - Only match what's EXPLICITLY in the CV:
   - DO NOT infer skills that aren't explicitly mentioned
   - If "Java" is in CV, match "Java" - but NOT "Spring Boot" unless mentioned
   - Be STRICT: only match if the keyword or its direct synonym appears in CV text
   
3. ALLOWED SEMANTIC MATCHING (very limited and correctly):
   - "AWS Lambda" → matches "AWS" and "Lambda" (it's the same thing)
   - "Spring Boot" → matches "Spring" (direct relationship)
   - DO NOT match across different cloud platforms (AWS ≠ GCP ≠ Azure, they are different)
   

4. CROSS-REFERENCE WITH CV:
   - Check skills section thoroughly
   - Check technologies mentioned in experience bullet points
   - Check tools/frameworks mentioned in projects
   - Consider certifications as proof of skills
   - Look at education for foundational knowledge

5. CATEGORIZE RESULTS:
   - Technical: Programming languages, frameworks, tools, platforms, databases
   - Soft Skills: Communication, leadership, collaboration, problem-solving, etc.

6. BE PRECISE AND RELEVANT:
   - ONLY include keywords that are EXPLICITLY mentioned in the CV
   - Do NOT infer or assume skills that aren't clearly stated
   - If JD mentions "GCP" but CV only has "AWS", do NOT match "GCP"
   - If JD mentions "Python" but CV only has "Java", do NOT match "Python"
   - If a skill is required in JD but not EXPLICITLY in CV, it's MISSING
   - When in doubt, mark it as MISSING rather than giving false credit

RETURN FORMAT:
Return ONLY this JSON structure (no markdown, no code blocks, no explanation):

{{
  "keywords_you_have": {{
    "technical": [
      "Python",
      "AWS",
      "Docker"
    ],
    "soft": [
      "Leadership",
      "Communication"
    ]
  }},
  "keywords_missing": {{
    "technical": [
      "Kubernetes",
      "React"
    ],
    "soft": [
      "Public Speaking"
    ]
  }}
}}

CRITICAL RULES:
1. Return ONLY the JSON object - no markdown formatting, no code blocks, no explanatory text
2. Use exact keyword names from the job description when possible
3. Be STRICT with matches - only give credit for EXPLICITLY mentioned skills
4. DO NOT infer skills from related technologies (AWS ≠ GCP, Java ≠ Python)
5. Empty arrays [] if no matches/missing in that category
6. Focus on what's TRULY required/mentioned in the JD
7. Technical skills should be specific (not generic like "programming")
8. Soft skills should be actionable (not vague like "good attitude")
9. When uncertain, mark as MISSING rather than giving false positive credit

BEGIN ANALYSIS NOW:
"""

def call_gemini_for_missing_keywords(structured_sections: dict, job_description: str) -> dict:
    """
    Call Gemini API to find missing keywords between CV and job description
    
    Args:
        structured_sections: Structured CV sections from MongoDB
        job_description: Raw job description text
        
    Returns:
        Dictionary with keywords_you_have and keywords_missing
    """
    model = initialize_gemini(service_type="keywords")
    prompt = create_missing_keywords_prompt(structured_sections, job_description)
    
    response = model.generate_content(prompt)
    response_text = response.text.strip()
    
    # Clean up response (remove markdown if present)
    if response_text.startswith('```'):
        lines = response_text.split('\n')
        response_text = '\n'.join(lines[1:-1])
        if response_text.startswith('json'):
            response_text = response_text[4:].strip()
    
    # Parse JSON
    result = json.loads(response_text)
    
    # Validate structure
    if "keywords_you_have" not in result:
        result["keywords_you_have"] = {"technical": [], "soft": []}
    if "keywords_missing" not in result:
        result["keywords_missing"] = {"technical": [], "soft": []}
    
    # Ensure nested keys exist
    for key in ["keywords_you_have", "keywords_missing"]:
        if "technical" not in result[key]:
            result[key]["technical"] = []
        if "soft" not in result[key]:
            result[key]["soft"] = []
    
    return result

def create_scoring_prompt(structured_sections: dict, job_description: str) -> str:
    """
    Create expert-level prompt for Gemini to score CV against job description
    
    Args:
        structured_sections: Structured CV sections from MongoDB
        job_description: Raw job description text
        
    Returns:
        Formatted prompt string
    """
    return f"""
You are an EXPERT CV EVALUATOR and RECRUITER with deep expertise in:
- Assessing candidate-job fit for technical roles
- Scoring CVs based on skills alignment, experience relevance, and content quality
- Providing actionable feedback for CV improvement
- Understanding ATS (Applicant Tracking Systems) optimization

YOUR MISSION:
Evaluate this candidate's CV against the job description and provide a comprehensive score breakdown.

CANDIDATE'S CV DATA (STRUCTURED):

Contact Information:
{json.dumps(structured_sections.get('contact', {}), indent=2)}

Skills:
{json.dumps(structured_sections.get('skills', {}), indent=2)}

Work Experience:
{json.dumps(structured_sections.get('experience', []), indent=2)}

Education:
{json.dumps(structured_sections.get('education', []), indent=2)}

Projects:
{json.dumps(structured_sections.get('projects', []), indent=2)}

Certifications:
{json.dumps(structured_sections.get('certifications', []), indent=2)}

JOB DESCRIPTION (FULL TEXT):
{job_description}

SCORING CRITERIA (100 POINTS TOTAL):

1. JOB MATCH SCORE (35 points maximum):
   - Technical skills alignment (20 pts): Count required skills in JD vs skills in CV
   - Soft skills alignment (10 pts): Leadership, communication, problem-solving mentioned
   - Domain knowledge (5 pts): Relevant industry/technology domain experience
   
   Calculation Logic:
   - Count total required technical skills in JD
   - Count how many the candidate HAS in their CV
   - Technical score = (skills_matched / skills_required) * 20
   - Evaluate soft skills similarly
   - Be STRICT: only count explicitly mentioned skills

2. EXPERIENCE RELEVANCE SCORE (30 points maximum):
   - Job titles similarity (10 pts): How similar are their past roles to this role?
   - Responsibilities alignment (15 pts): Do their past duties match JD requirements?
   - Industry/company relevance (5 pts): Tech company vs non-tech, startup vs enterprise
   
   Calculation Logic:
   - Analyze job titles in CV vs required role
   - Compare responsibilities in experience bullets vs JD requirements
   - Consider years of experience if mentioned in JD

3. CONTENT QUALITY SCORE (20 points maximum):
   - Bullet points structure (5 pts): Uses bullet points vs long paragraphs
   - Action verbs (5 pts): Strong verbs like "Led", "Developed", "Implemented"
   - Quantifiable metrics (7 pts): Numbers, percentages, impact metrics present
   - Clarity and professionalism (3 pts): Clear, concise, professional tone
   
   Calculation Logic:
   - Check if experience uses bullet points (good) vs paragraphs (bad)
   - Count action verbs in bullets
   - Count quantifiable achievements (e.g., "reduced latency by 40%")
   - Evaluate overall clarity

4. ATS & KEYWORDS SCORE (15 points maximum):
   - CV completeness (5 pts): Has contact, education, experience, skills sections
   - Keyword presence (7 pts): JD keywords appear naturally in CV
   - Structure and organization (3 pts): Logical flow, no critical gaps
   
   Calculation Logic:
   - Check for required sections (contact, education, experience, skills)
   - Count how many JD keywords appear in CV
   - Evaluate overall structure quality

OVERALL RATING TIERS:
- 90-100: "Excellent Match — Apply with Confidence"
- 80-89: "Good Match — Competitive Candidate"
- 70-79: "Decent Match — Fix Gaps to Compete"
- 60-69: "Fair Match — Needs Work"
- Below 60: "Poor Match — Major Revisions Needed"

RETURN FORMAT:
Return ONLY this JSON structure (no markdown, no code blocks, no explanation):

{{
  "overall_score": 72,
  "max_score": 100,
  "rating": "Decent Match — Fix Gaps to Compete",
  "category_scores": {{
    "job_match": {{
      "score": 22,
      "max_score": 35,
      "percentage": 63,
      "explanation": "Brief 1-2 sentence explanation of why this score"
    }},
    "experience_relevance": {{
      "score": 20,
      "max_score": 30,
      "percentage": 67,
      "explanation": "Brief 1-2 sentence explanation"
    }},
    "content_quality": {{
      "score": 18,
      "max_score": 20,
      "percentage": 90,
      "explanation": "Brief 1-2 sentence explanation"
    }},
    "ats_keywords": {{
      "score": 12,
      "max_score": 15,
      "percentage": 80,
      "explanation": "Brief 1-2 sentence explanation"
    }}
  }},
  "strengths": [
    "Specific strength 1",
    "Specific strength 2",
    "Specific strength 3"
  ],
  "gaps": [
    "Specific gap 1",
    "Specific gap 2",
    "Specific gap 3"
  ],
  "recommendations": [
    "Actionable recommendation 1",
    "Actionable recommendation 2",
    "Actionable recommendation 3"
  ]
}}

CRITICAL RULES:
1. Return ONLY the JSON object - no markdown, no code blocks, no explanatory text
2. Calculate scores mathematically based on the logic provided
3. Overall score MUST equal sum of all category scores
4. Percentages should be calculated as (score/max_score)*100 and rounded
5. Provide 3-5 specific strengths (what's working well)
6. Provide 3-5 specific gaps (what's missing or weak)
7. Provide 3-5 actionable recommendations (how to improve)
8. Be honest and constructive - help the candidate improve
9. Rating tier must match the overall_score range

BEGIN EVALUATION NOW:
"""

def call_gemini_for_score(structured_sections: dict, job_description: str) -> dict:
    """
    Call Gemini API to score CV against job description
    
    Args:
        structured_sections: Structured CV sections from MongoDB
        job_description: Raw job description text
        
    Returns:
        Dictionary with overall_score, category_scores, strengths, gaps, recommendations
    """
    model = initialize_gemini(service_type="score")
    prompt = create_scoring_prompt(structured_sections, job_description)
    
    response = model.generate_content(prompt)
    response_text = response.text.strip()
    
    # Clean up response (remove markdown if present)
    if response_text.startswith('```'):
        lines = response_text.split('\n')
        response_text = '\n'.join(lines[1:-1])
        if response_text.startswith('json'):
            response_text = response_text[4:].strip()
    
    # Parse JSON
    result = json.loads(response_text)
    
    # Validate structure
    if "overall_score" not in result:
        result["overall_score"] = 0
    if "max_score" not in result:
        result["max_score"] = 100
    if "rating" not in result:
        result["rating"] = "Unknown"
    if "category_scores" not in result:
        result["category_scores"] = {}
    if "strengths" not in result:
        result["strengths"] = []
    if "gaps" not in result:
        result["gaps"] = []
    if "recommendations" not in result:
        result["recommendations"] = []
    
    return result

def create_tailored_bullets_prompt(job_description: str, similar_chunks: list) -> str:
    """
    Create expert-level prompt for Gemini to generate tailored CV bullet points
    
    Uses XYZ format: Action Verb (X) + Task/Action (Y) + Quantifiable Result (Z)
    
    Args:
        job_description: Raw job description text
        similar_chunks: List of similar CV chunks with text, section, cv_id, score
        
    Returns:
        Formatted prompt string
    """
    # Format chunks for prompt
    chunks_text = ""
    for i, chunk in enumerate(similar_chunks, 1):
        section = chunk.get("section", "unknown")
        text = chunk.get("text", "")
        score = chunk.get("score", 0.0)
        chunks_text += f"\nChunk {i} (Section: {section}, Relevance: {score:.2f}):\n{text}\n"
    
    return f"""
You are an EXPERT RESUME WRITER and CAREER COACH with deep expertise in:
- Writing compelling, ATS-optimized resume bullet points
- Using the XYZ format (Action Verb + Task + Quantifiable Result)
- Tailoring bullet points to match job requirements
- Highlighting technical skills and achievements effectively
- Creating impact-driven statements that stand out to recruiters

YOUR MISSION:
Generate 5-6 tailored, professional resume bullet points based on the job description requirements and relevant CV chunks from RELEVANT CV CHUNKS below, anaylze those chunks to create tailor bullet points.

Tip: As you may know after you aanayzle and understand, those chunks high score could be from experience, and project that would be effective for you to generate bullet points. (it's like doing RAG with those chunks data from vector to create more tailored and effective response)

DO NOT generate generic bullets. Base your bullets on the ACTUAL content in the chunks below to create tailor bullet points.

JOB DESCRIPTION:
{job_description}

RELEVANT CV CHUNKS (from semantic search - various sections):
{chunks_text}

CRITICAL REQUIREMENTS - XYZ FORMAT:

Every bullet point MUST follow the XYZ format:
- X = Strong Action Verb (Led, Developed, Implemented, Designed, Optimized, etc.)
- Y = Specific Task/Action (What you did, technology used, scope)
- Z = Quantifiable Result/Impact (Numbers, percentages, metrics, outcomes)

EXAMPLES OF EXCELLENT XYZ BULLETS:
 "Led development of microservices architecture using FastAPI and Docker, reducing API latency by 40% and improving system scalability"
 "Implemented CI/CD pipelines with Jenkins and Kubernetes, automating deployments and reducing release time from 2 days to 2 hours"
 "Designed and developed RESTful APIs handling 10M+ requests daily, improving response time by 50% through query optimization"
 "Optimized database queries and indexing strategies, reducing query execution time from 500ms to 50ms and cutting infrastructure costs by 30%"
 "Collaborated with cross-functional teams of 8+ engineers to deliver features 20% faster using Agile methodologies"

BAD EXAMPLES (AVOID):
 "Worked on APIs" (no action verb, no metrics)
 "Developed software" (too vague, no impact)
 "Used Python" (not a bullet point, no context)

BULLET POINT GUIDELINES:

1. ACTION VERBS (X):
   - Use strong, specific verbs: Led, Developed, Implemented, Designed, Optimized, Built, Created, Architected, Deployed, Automated
   - Avoid weak verbs: Worked, Did, Used, Helped, Assisted (unless necessary)

2. TASK/ACTION (Y):
   - Be specific about technology, tools, frameworks mentioned in JD
   - Include scope: team size, project scale, system complexity
   - Reference relevant skills from job description

3. QUANTIFIABLE RESULT (Z):
   - ALWAYS include numbers: percentages, counts, time reductions, cost savings
   - Show impact: "improved by X%", "reduced by Y", "handled Z requests"
   - If exact numbers aren't available, use reasonable estimates based on context

4. LENGTH:
   - Each bullet: 1-2 lines maximum
   - Concise but impactful
   - No fluff or filler words

5. RELEVANCE & SOURCE MATERIAL:
   - CRITICAL: Use the ACTUAL text from the chunks provided above
   - Each chunk shows its section (experience, projects, skills, etc.) and relevance score
   - Prioritize chunks with higher relevance scores (closer to 1.0)
   - Extract key achievements, technologies, and metrics from the chunk text
   - Combine related chunks from different sections to create comprehensive bullets
   - DO NOT invent information - work with what's in the chunks

6. VARIETY:
   - Mix different types: technical achievements, leadership, optimization, collaboration
   - Cover different aspects: development, deployment, optimization, team work
   - Use chunks from different sections (experience, projects, etc.) to show breadth

7. USING THE CHUNK TEXT:
   - Read each chunk carefully - it contains real experience/project details
   - Extract specific technologies, achievements, and metrics from chunk text
   - Transform chunk content into polished XYZ-format bullets
   - If a chunk mentions "Built REST API with FastAPI", use that in your bullet
   - If a chunk has metrics (e.g., "reduced latency by 40%"), include them
   - Enhance and polish, but stay true to the chunk content

OUTPUT FORMAT:
Return ONLY a JSON array of bullet point strings (no markdown, no code blocks, no explanation):

[
  "Led development of microservices using FastAPI, reducing API latency by 40%",
  "Implemented CI/CD pipelines with Docker and Kubernetes, improving deployment speed by 3x",
  "Designed RESTful APIs handling 10M+ requests daily with 99.9% uptime",
  "Optimized database queries reducing response time from 500ms to 50ms",
  "Collaborated with cross-functional teams to deliver features 20% faster"
]

CRITICAL RULES:
1. Return ONLY the JSON array - no markdown, no code blocks, no explanatory text
2. Generate exactly 5-6 bullet points (prefer 6 if you have enough context)
3. Each bullet MUST follow XYZ format with quantifiable results
4. Use strong action verbs and specific technical details
5. Make bullets ready to use - professional, polished, ATS-friendly
6. Base bullets on the provided chunks, but enhance them to match JD requirements
7. If chunks don't provide enough context, create realistic bullets that align with JD requirements

BEGIN GENERATION NOW:
"""

def call_gemini_for_tailored_bullets(job_description: str, similar_chunks: list) -> dict:
    """
    Call Gemini API to generate tailored bullet points
    
    Args:
        job_description: Raw job description text
        similar_chunks: List of similar CV chunks with text, section, cv_id, score
        
    Returns:
        Dictionary with tailored_bullets list
    """
    model = initialize_gemini(service_type="bullets")
    prompt = create_tailored_bullets_prompt(job_description, similar_chunks)
    
    response = model.generate_content(prompt)
    response_text = response.text.strip()
    
    # Clean up response (remove markdown if present)
    if response_text.startswith('```'):
        lines = response_text.split('\n')
        response_text = '\n'.join(lines[1:-1])
        if response_text.startswith('json'):
            response_text = response_text[4:].strip()
    
    # Parse JSON
    try:
        bullets = json.loads(response_text)
        if not isinstance(bullets, list):
            raise ValueError("Response is not a list")
        
        # Validate bullets
        validated_bullets = []
        for bullet in bullets:
            if isinstance(bullet, str) and bullet.strip():
                validated_bullets.append(bullet.strip())
        
        if len(validated_bullets) < 3:
            raise ValueError(f"Expected at least 3 bullets, got {len(validated_bullets)}")
        
        return {
            "tailored_bullets": validated_bullets,
            "count": len(validated_bullets)
        }
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse Gemini response as JSON: {e}\nResponse: {response_text}")
    except Exception as e:
        raise ValueError(f"Failed to process tailored bullets: {e}")


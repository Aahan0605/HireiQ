// Central data store for candidates with session persistence
const DEFAULT_CANDIDATES = [
  { 
    id: '1', 
    name: 'Alice Chen', 
    role: 'Senior Frontend Engineer', 
    email: 'alice.chen@example.com', 
    github: 'github.com/alicec', 
    linkedin: 'linkedin.com/in/alicechen', 
    location: 'San Francisco, CA', 
    score: 94, 
    status: 'Strong Match',
    date: '1 day ago',
    skills: ['React', 'TypeScript', 'Next.js', 'Tailwind CSS', 'JavaScript', 'CSS', 'HTML', 'Figma'],
    summary: 'Alice is a robust front-end specialist with a history of scaling design systems and optimizing web performance. Her GitHub activity indicates strong modern React adoption (Hooks, RSC, Next.js). There is a slight gap in container orchestration, but her infrastructure knowledge is sufficient for frontend DevOps.',
    experience: [
      { company: 'Acme Corp', title: 'Senior Staff UI Engineer', date: '2021 - Present', description: 'Led the development of a unified design system reducing UI inconsistencies by 40%. Implemented performance improvements yielding a 25% increase in Lighthouse score.' },
      { company: 'Globex Inc', title: 'Frontend Developer', date: '2019 - 2021', description: 'Architected high-performance React applications and mentored junior developers.' }
    ]
  },
  { 
    id: '2', 
    name: 'Marcus Jones', 
    role: 'Fullstack Engineer', 
    email: 'marcus.j@example.com', 
    github: 'github.com/mjones-dev', 
    linkedin: 'linkedin.com/in/marcusj', 
    location: 'Austin, TX', 
    score: 88, 
    status: 'Match',
    date: '2 days ago',
    skills: ['Node.js', 'TypeScript', 'React', 'PostgreSQL', 'Docker', 'WebSocket', 'JavaScript', 'Express'],
    summary: 'Marcus possesses a balanced full-stack skill set with deep proficiency in Node.js and TypeScript. His experience at high-growth startups makes him a great cultural fit for fast-paced agile teams.',
    experience: [
      { company: 'StartupX', title: 'Fullstack Engineer', date: '2022 - Present', description: 'Built and scaled real-time collaboration tools using WebSockets and Node.js.' }
    ]
  },
  { 
    id: '3', 
    name: 'Sofia Rodriguez', 
    role: 'Backend Lead', 
    email: 'sofia.r@example.com', 
    github: 'github.com/srodrig', 
    linkedin: 'linkedin.com/in/sofiar', 
    location: 'New York, NY', 
    score: 97, 
    status: 'Strong Match',
    date: '2 hours ago',
    skills: ['Go', 'gRPC', 'PostgreSQL', 'Kubernetes', 'AWS', 'Distributed Systems', 'Terraform', 'Docker'],
    summary: 'Sofia is an exceptional backend lead with expertise in distributed systems and Go. She has a proven track record of reducing latency in high-traffic APIs by over 60% through strategic caching and DB optimization.',
    experience: [
      { company: 'CloudScale', title: 'Staff Software Engineer', date: '2020 - Present', description: 'Optimized high-throughput gRPC services and managed cross-functional engineering pods.' }
    ]
  },
  { 
    id: '7', 
    name: 'Tirth Patel', 
    role: 'Fullstack & Web3 Engineer', 
    email: 'tirth_patel@example.com', 
    github: 'github.com/tirthpatel', 
    linkedin: 'linkedin.com/in/tirthpatel', 
    location: 'Ahmedabad, India', 
    score: 98, 
    status: 'Strong Match',
    date: 'Just now',
    skills: ['Solidity', 'React', 'Django', 'Node.js', 'Web3', 'Python', 'JavaScript', 'LLaMA', 'AI', 'Agentic Systems'],
    summary: 'Highly skilled B.Tech candidate from Nirma University (Expected 2028). Winner of the Codeversity National Hackathon at IIT Gandhinagar. Deeply proficient in Web3 (Solidity), Agentic AI (LLaMA 3.1, Groq), and Fullstack development (React, Django, Node.js). Proven track record of building production-grade AI systems and decentralized platforms.',
    experience: [
      { company: 'Nirma University', title: 'Student Researcher', date: '2024 - Present', description: 'Developing agentic AI systems and exploring decentralized finance protocols.' }
    ]
  },
];

// Key for localStorage
const STORAGE_KEY = 'hireiq_dynamic_candidates';

/**
 * Gets all candidates, merging defaults with session-stored ones.
 */
export const getAllCandidates = () => {
  if (typeof window === 'undefined') return DEFAULT_CANDIDATES;
  
  const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
  // Avoid duplicates if user refreshes but same IDs are there
  const merged = [...DEFAULT_CANDIDATES];
  
  stored.forEach(storedCand => {
    if (!merged.find(c => c.id === storedCand.id)) {
      merged.unshift(storedCand); // New ones at the top
    }
  });
  
  return merged;
};

/**
 * Finds a single candidate by ID.
 */
export const getCandidateById = (id) => {
  return getAllCandidates().find(c => c.id === id);
};

/**
 * Simulates analyzing a file and creating a new candidate profile.
 */
export const addCandidateFromCV = async (file) => {
  const newId = `new-${Date.now()}`;
  const rawName = file.name.replace(/\.[^/.]+$/, "").replace(/_/g, " ").replace(/-/g, " ");
  // Capitalize name
  const fileName = rawName.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');

  const formData = new FormData();
  formData.append('file', file);
  
  let extractedText = "";
  let features = { skills: [], experience: 0.0 };

  try {
    const res = await fetch("http://localhost:8001/api/v1/candidates/upload-resume", {
      method: "POST",
      body: formData
    });
    if (res.ok) {
      const data = await res.json();
      extractedText = data.extracted_text || "";
      if (data.features) {
        features = data.features;
      }
    }
  } catch (e) {
    console.error("Failed to upload resume to backend:", e);
  }

  // Extract Email
  const emailMatch = extractedText.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/);
  const email = emailMatch ? emailMatch[0] : `${rawName.toLowerCase().replace(/\s/g, '.')}@example.com`;

  // Extract GitHub
  const githubMatch = extractedText.match(/github\.com\/[a-zA-Z0-9_-]+/i);
  const github = githubMatch ? githubMatch[0] : `github.com/${rawName.toLowerCase().replace(/\s/g, '')}`;

  // Extract LinkedIn
  const linkedinMatch = extractedText.match(/linkedin\.com\/in\/[a-zA-Z0-9_-]+/i);
  const linkedin = linkedinMatch ? linkedinMatch[0] : `linkedin.com/in/${rawName.toLowerCase().replace(/\s/g, '')}`;

  // Extract Experience Array from Text
  let experiences = [];
  if (extractedText) {
    const lines = extractedText.split('\n');
    let inExperience = false;
    let currentExp = null;
    
    // First Pass: Try to find an explicit Experience section
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;
        
        const lowerLine = line.toLowerCase();
        if (lowerLine === 'experience' || lowerLine === 'work experience' || lowerLine === 'employment history' || lowerLine === 'professional experience') {
            inExperience = true;
            continue;
        }
        
        if (inExperience) {
            if (lowerLine === 'education' || lowerLine === 'skills' || lowerLine === 'projects' || lowerLine === 'summary' || lowerLine === 'certifications') {
                inExperience = false;
                if (currentExp && currentExp.title) experiences.push(currentExp);
                currentExp = null;
                continue;
            }
            
            // Check for dates like 2020, 2021, Present, etc.
            const dateMatch = line.match(/(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|[a-zA-Z]+)?\s*\d*(?:199\d|200\d|201\d|202\d)\s*[-–to]+\s*(?:Present|Current|Now|Till Date|[a-zA-Z]+)?\s*\d*(?:199\d|200\d|201\d|202\d|Present|Current|Now)?/i) || line.match(/\b(20\d{2}|19\d{2})\b/i);
            const hasBullet = line.startsWith('-') || line.startsWith('•') || line.startsWith('*');
            
            if (dateMatch && !hasBullet && line.length < 100) { // Likely a header line
                if (currentExp && currentExp.title) experiences.push(currentExp);
                
                let title = line.replace(dateMatch[0], '').trim();
                let company = 'Unknown Company';
                
                if (lines[i-1] && !lines[i-1].match(/\b(20\d{2}|19\d{2})\b/)) {
                    title = lines[i-1].trim();
                    company = line.replace(dateMatch[0], '').replace(/\|/g, '').trim() || 'Tech Corp';
                } else if (!title) {
                    title = lines[i+1] ? lines[i+1].trim() : 'Software Engineer';
                }
                
                currentExp = {
                    title: title.substring(0, 70).trim(),
                    company: company.substring(0, 50).trim(),
                    date: dateMatch[0],
                    description: ''
                };
            } else if (currentExp) {
                if (hasBullet) {
                    currentExp.description += line.replace(/^[•*-]\s*/, '') + ' ';
                } else if (line.length > 20 && !dateMatch) {
                    currentExp.description += line + ' ';
                }
            }
        }
    }
    if (currentExp && currentExp.title) experiences.push(currentExp);
    
    // Second Pass: If explicit section parsing failed, do a global regex scan
    if (experiences.length === 0) {
        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const match = line.match(/\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|[a-zA-Z]+)?\s*\d*(?:199\d|200\d|201\d|202\d)\s*[-–to]+\s*(?:Present|Current|Now|till|[a-zA-Z]+)?\s*\d*(?:199\d|200\d|201\d|202\d|Present|Current|Now)?\b/i);
            if (match && line.length < 100) {
                const dateStr = match[0];
                const cleaned = line.replace(dateStr, '').trim();
                const roleAndCompany = cleaned.length > 5 ? cleaned : (lines[i-1] ? lines[i-1].trim() : 'Software Engineer');
                
                let title = roleAndCompany;
                let company = 'Company';
                if (roleAndCompany.includes(' at ')) {
                    [title, company] = roleAndCompany.split(' at ');
                } else if (roleAndCompany.includes('|')) {
                    [title, company] = roleAndCompany.split('|');
                } else if (lines[i-1] && lines[i-1].trim().length > 0 && !lines[i-1].match(/\b(199\d|200\d|201\d|202\d)\b/)) {
                    title = lines[i-1].trim();
                    company = line.replace(dateStr, '').trim() || 'Software Company';
                }

                let desc = '';
                for (let j = i+1; j < Math.min(i+10, lines.length); j++) {
                    if (lines[j].match(/\b(199\d|200\d|201\d|202\d)\b/i)) break;
                    if (lines[j].toLowerCase().startsWith('education') || lines[j].toLowerCase().startsWith('skills')) break;
                    const textLine = lines[j].trim();
                    if (textLine.length > 10) {
                        desc += textLine.replace(/^[•*-]\s*/, '') + ' ';
                    }
                }

                if (!experiences.find(e => e.date === dateStr)) {
                    experiences.push({
                        title: title.substring(0, 70).trim(), 
                        company: company.substring(0, 50).trim(), 
                        date: dateStr, 
                        description: desc.substring(0, 200).trim() + (desc.length > 200 ? '...' : '')
                    });
                }
            }
        }
    }
  }

  // Fallback Experience
  if (experiences.length === 0) {
    experiences.push({
      company: 'CV Analyser',
      title: 'Parsed Candidate',
      date: 'Recent',
      description: 'Experience timeline could not be parsed automatically. Please check the uploaded document manually.'
    });
  }
  
  // Predict Role and Adjust Score Predictively based on text
  const lowerText = extractedText.toLowerCase() || fileName.toLowerCase();
  let role = 'Software Engineer';

  if (lowerText.includes('react') || lowerText.includes('frontend')) {
    role = 'Frontend Specialist';
  } else if (lowerText.includes('blockchain') || lowerText.includes('web3') || lowerText.includes('solidity')) {
    role = 'Web3 Engineer';
  } else if (lowerText.includes('ai') || lowerText.includes('machine learning') || lowerText.includes('data structure') || lowerText.includes('deep learning')) {
    role = 'AI/ML Engineer';
  } else if (lowerText.includes('node') || lowerText.includes('backend') || lowerText.includes('python') || lowerText.includes('c++')) {
    role = 'Backend Engineer';
  }

  // Calculate Match Score based on Target Keywords directly mapped to the inferred job role
  const roleKeywords = {
    'Frontend Specialist': ['react', 'vue', 'angular', 'javascript', 'typescript', 'html', 'css', 'tailwind', 'ui/ux', 'next.js', 'webpack'],
    'Backend Engineer': ['node', 'python', 'java', 'go', 'c++', 'sql', 'nosql', 'docker', 'kubernetes', 'aws', 'api', 'microservices'],
    'Web3 Engineer': ['solidity', 'ethereum', 'smart contract', 'blockchain', 'web3', 'rust', 'cryptos', 'defi', 'truffle', 'hardhat'],
    'AI/ML Engineer': ['python', 'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'nlp', 'data science', 'ai', 'computer vision', 'data structure', 'algorithms', 'pandas'],
    'Software Engineer': ['javascript', 'python', 'java', 'git', 'agile', 'sql', 'docker', 'aws', 'rest', 'oop', 'data structures']
  };

  const expectedKeywords = roleKeywords[role] || roleKeywords['Software Engineer'];
  let keywordMatches = 0;
  
  expectedKeywords.forEach(kw => {
    // Exact or loose match in text
    if (lowerText.includes(kw)) {
      keywordMatches++;
    }
  });
  
  // Calculate a strict, accurate match percentage against the job role's required skills
  // Adding a slight baseline (e.g. 50%) plus up to 45% based on keyword overlap
  const matchPercentage = Math.round((keywordMatches / expectedKeywords.length) * 45);
  const baseline = 50;
  
  let score = baseline + matchPercentage;
  
  // Experience bonus: if they have more dates, they probably have more experience
  if (experiences.length > 2) score += 3;
  if (experiences.length > 4) score += 2;
  
  // Cap at 99
  score = Math.min(99, score);
  const baseScore = score;

  // Extract a real summary from the CV text (First meaty paragraph)
  let extractedSummary = '';
  if (extractedText) {
    const lines = extractedText.split('\n');
    let inSummary = false;
    let summaryText = '';
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      
      const lowerLine = line.toLowerCase();
      // Detect start of summary section
      if (!inSummary && (lowerLine === 'summary' || lowerLine === 'profile' || lowerLine === 'about me' || lowerLine === 'professional summary')) {
        inSummary = true;
        continue;
      }
      
      if (inSummary) {
        // Break out of summary if we hit another standard section or an empty block
        if (lowerLine === 'education' || lowerLine === 'experience' || lowerLine === 'skills' || line.match(/\b(201\d|202\d)\b/)) {
          break;
        }
        if (line.length > 20) {
          summaryText += line + ' ';
        }
      }
    }
    
    // If no explicit summary header, grab the first paragraph that looks substantial, isn't contact info, and isn't coursework
    if (!summaryText) {
      const firstLongLine = lines.find(l => 
        l.trim().length > 60 && 
        !l.toLowerCase().includes('github.com') && 
        !l.includes('@') &&
        !l.toLowerCase().includes('coursework') &&
        !l.toLowerCase().includes('education')
      );
      if (firstLongLine) {
        summaryText = firstLongLine.trim();
      }
    }
    extractedSummary = summaryText.substring(0, 400).trim();
    if (summaryText.length > 400) extractedSummary += '...';
  }

  let finalSummary = extractedSummary 
    ? extractedSummary 
    : `This candidate exhibits a solid foundation as a ${role}. Automated feature extraction identified key technical competencies. Based on the CV, they have approximately ${features.experience || 'several'} years of relevant experience. Overall match score of ${score}% makes them a fit.`;

  // Calculate dynamic radar graph data based on skill frequency
  let radarData = [];
  if (features.skills && features.skills.length > 0) {
    const topSkills = features.skills.slice(0, 6);
    
    radarData = topSkills.map(skill => {
      // Find frequency of this skill in the text to derive mastery confidence
      const regex = new RegExp(`\\b${skill.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'gi');
      const matches = extractedText.match(regex);
      const occurrences = matches ? matches.length : 1;
      
      // Calculate a realistic score: 1 mention = baseScore - 10, more mentions = up to 98
      const calculatedScore = Math.min(98, Math.max(65, baseScore + (occurrences * 4) - 10));
      
      return { 
        subject: skill.substring(0, 12), 
        A: calculatedScore, 
        fullMark: 100 
      };
    });
    
    // Pad to 6 if needed
    const defaultSubjects = ['Problem Solving', 'Architecture', 'Testing', 'DevOps', 'Agile', 'System Design'];
    while (radarData.length < 6) {
      radarData.push({ 
        subject: defaultSubjects[radarData.length] || `Skill ${radarData.length + 1}`, 
        A: Math.max(60, baseScore - 15), 
        fullMark: 100 
      });
    }
  }

  const newCandidate = {
    id: newId,
    name: fileName,
    role: role,
    email: email,
    github: github,
    linkedin: linkedin,
    location: 'Remote',
    score: score,
    status: score > 90 ? 'Strong Match' : 'Match',
    date: 'Just now',
    summary: finalSummary,
    experience: experiences.slice(0, 4),
    skills: features.skills || [],
    radarData: radarData, // Save the dynamic radar data directly
    baseScore: score
  };

  const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
  localStorage.setItem(STORAGE_KEY, JSON.stringify([...stored, newCandidate]));
  
  return newCandidate;
};

class HiringAgentApp {
    constructor() {
        this.currentAnalysisId = null;
        this.websocket = null;
        this.uploadedResumeData = null;
        this.parsedJobData = null;
        this.initializeEventListeners();
        this.initializeSliders();
        this.initializeFileUpload();
    }

    initializeEventListeners() {
        document.getElementById('startAnalysis').addEventListener('click', () => this.startAnalysis());
        
        // Only add change file button listener if it exists
        const changeFileBtn = document.getElementById('changeFileBtn');
        if (changeFileBtn) {
            changeFileBtn.addEventListener('click', () => this.resetFileUpload());
        }
    }

    initializeSliders() {
        const sliders = [
            'resumeJdMatch', 'githubAnalysis', 'linkedinAnalysis', 
            'technicalBlogs', 'projectQuality', 'workExperience'
        ];

        sliders.forEach(sliderId => {
            const slider = document.getElementById(sliderId);
            const valueSpan = document.getElementById(sliderId + 'Value');
            
            slider.addEventListener('input', (e) => {
                valueSpan.textContent = e.target.value;
            });
        });
    }

    initializeFileUpload() {
        const fileInput = document.getElementById('resumeFileInput');
        const dragDropArea = document.getElementById('dragDropArea');
        
        console.log('Initializing file upload...', { fileInput, dragDropArea });
        
        if (!fileInput) {
            console.error('File input not found!');
            return;
        }
        
        // File input change - this is the main functionality
        fileInput.addEventListener('change', (e) => {
            console.log('File input changed:', e.target.files);
            if (e.target.files.length > 0) {
                const file = e.target.files[0];
                console.log('File selected:', file.name, file.size, file.type);
                this.handleFileUpload(file);
            }
        });
        
        // Optional: Add drag and drop to the drag drop area if it exists
        if (dragDropArea) {
            // Show drag drop area after first use or on hover
            fileInput.addEventListener('focus', () => {
                dragDropArea.classList.remove('hidden');
            });
            
            // Drag and drop events
            dragDropArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dragDropArea.classList.add('border-primary', 'bg-blue-50');
            });
            
            dragDropArea.addEventListener('dragleave', (e) => {
                e.preventDefault(); 
                e.stopPropagation();
                dragDropArea.classList.remove('border-primary', 'bg-blue-50');
            });
            
            dragDropArea.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation();
                dragDropArea.classList.remove('border-primary', 'bg-blue-50');
                
                if (e.dataTransfer.files.length > 0) {
                    const file = e.dataTransfer.files[0];
                    console.log('File dropped:', file.name);
                    // Set the file to the input and trigger change
                    const dt = new DataTransfer();
                    dt.items.add(file);
                    fileInput.files = dt.files;
                    this.handleFileUpload(file);
                }
            });
            
            // Click on drag area to trigger file input
            dragDropArea.addEventListener('click', () => {
                fileInput.click();
            });
        }
        
        // Add change file functionality
        const changeFileBtn = document.getElementById('changeFileBtn');
        if (changeFileBtn) {
            changeFileBtn.addEventListener('click', () => {
                this.resetFileUpload();
                fileInput.click();
            });
        }
    }

    async handleFileUpload(file) {
        // Validate file
        const maxSize = 10 * 1024 * 1024; // 10MB
        const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
        
        if (file.size > maxSize) {
            alert('File size must be less than 10MB');
            return;
        }
        
        if (!allowedTypes.includes(file.type) && !file.name.toLowerCase().match(/\.(pdf|doc|docx|txt)$/)) {
            alert('Please upload a PDF, DOC, DOCX, or TXT file');
            return;
        }
        
        // Show progress
        this.showUploadProgress();
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch('/api/parse-resume', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to parse resume');
            }
            
            const result = await response.json();
            this.uploadedResumeData = result;
            this.showUploadSuccess(file.name, result.structured_data);
            
        } catch (error) {
            console.error('Upload error:', error);
            alert(`Failed to parse resume: ${error.message}`);
            this.resetFileUpload();
        }
    }

    showUploadProgress() {
        document.getElementById('uploadProgress').classList.remove('hidden');
        document.getElementById('uploadSuccess').classList.add('hidden');
        document.getElementById('parsedResumeData').classList.add('hidden');
        
        // Simulate progress
        let progress = 0;
        const progressBar = document.getElementById('progressBar');
        const interval = setInterval(() => {
            progress += Math.random() * 30;
            if (progress > 90) progress = 90;
            progressBar.style.width = progress + '%';
        }, 200);
        
        // Store interval ID to clear it later
        this.progressInterval = interval;
    }

    showUploadSuccess(filename, structuredData) {
        // Clear progress interval
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
        
        document.getElementById('uploadProgress').classList.add('hidden');
        document.getElementById('uploadSuccess').classList.remove('hidden');
        document.getElementById('parsedResumeData').classList.remove('hidden');
        
        // Show filename
        document.getElementById('uploadedFileName').textContent = filename;
        
        // Display extracted data
        document.getElementById('extractedName').textContent = structuredData.candidate_name || 'Not found';
        document.getElementById('extractedEmail').textContent = structuredData.email || 'Not found';
        document.getElementById('extractedExperience').textContent = 
            structuredData.experience_years ? `${structuredData.experience_years} years` : 'Not specified';
        document.getElementById('extractedSkills').textContent = 
            structuredData.skills ? structuredData.skills.slice(0, 3).join(', ') + (structuredData.skills.length > 3 ? '...' : '') : 'Not found';
            
        // Pre-fill social profiles if any
        if (structuredData.social_profiles && structuredData.social_profiles.length > 0) {
            const socialUrls = structuredData.social_profiles.map(p => p.url).join('\n');
            document.getElementById('manualSocialProfiles').value = socialUrls;
        }
    }

    resetFileUpload() {
        // Clear progress interval
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
        
        document.getElementById('uploadProgress').classList.add('hidden');
        document.getElementById('uploadSuccess').classList.add('hidden');
        document.getElementById('parsedResumeData').classList.add('hidden');
        
        document.getElementById('resumeFileInput').value = '';
        document.getElementById('progressBar').style.width = '0%';
        this.uploadedResumeData = null;
        
        // Clear manual fields
        document.getElementById('manualName').value = '';
        document.getElementById('manualEmail').value = '';
        document.getElementById('manualSocialProfiles').value = '';
    }

    async startAnalysis() {
        if (!this.validateForm()) {
            return;
        }

        const analysisData = this.collectFormData();
        
        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(analysisData)
            });

            if (!response.ok) {
                throw new Error('Failed to start analysis');
            }

            const result = await response.json();
            this.currentAnalysisId = result.analysis_id;
            
            this.showProgressSection();
            this.connectWebSocket();
            
        } catch (error) {
            console.error('Error starting analysis:', error);
            alert('Failed to start analysis. Please try again.');
        }
    }

    validateForm() {
        // Check if job description is provided
        const jobDescriptionText = document.getElementById('jobDescriptionText').value.trim();
        if (!jobDescriptionText) {
            alert('Please provide a job description.');
            document.getElementById('jobDescriptionText').focus();
            return false;
        }

        // Check if resume is uploaded
        if (!this.uploadedResumeData) {
            alert('Please upload a resume file.');
            return false;
        }

        return true;
    }

    collectFormData() {
        const customWeights = {
            resume_jd_match: parseFloat(document.getElementById('resumeJdMatch').value),
            github_analysis: parseFloat(document.getElementById('githubAnalysis').value),
            linkedin_analysis: parseFloat(document.getElementById('linkedinAnalysis').value),
            technical_blogs: parseFloat(document.getElementById('technicalBlogs').value),
            project_quality: parseFloat(document.getElementById('projectQuality').value),
            work_experience: parseFloat(document.getElementById('workExperience').value)
        };

        // Parse job description using AI
        const jobDescriptionText = document.getElementById('jobDescriptionText').value.trim();
        const parsedJobData = this.parseJobDescription(jobDescriptionText);

        // Get resume data from uploaded file
        const structuredData = this.uploadedResumeData.structured_data;
        
        // Apply manual overrides if provided
        const manualName = document.getElementById('manualName').value.trim();
        const manualEmail = document.getElementById('manualEmail').value.trim();
        const manualSocialProfiles = document.getElementById('manualSocialProfiles').value.trim();
        
        // Process social profiles
        let socialProfiles = structuredData.social_profiles || [];
        if (manualSocialProfiles) {
            const additionalProfiles = manualSocialProfiles
                .split('\n')
                .filter(url => url.trim())
                .map(url => {
                    url = url.trim();
                    let platform = 'other';
                    
                    if (url.includes('github.com')) platform = 'github';
                    else if (url.includes('linkedin.com')) platform = 'linkedin';
                    else if (url.includes('twitter.com') || url.includes('x.com')) platform = 'twitter';
                    else if (url.includes('medium.com')) platform = 'medium';
                    
                    return { platform, url };
                });
            socialProfiles = [...socialProfiles, ...additionalProfiles];
        }

        return {
            job_description: {
                title: parsedJobData.title,
                company: parsedJobData.company,
                description: jobDescriptionText,
                requirements: parsedJobData.requirements,
                preferred_skills: parsedJobData.preferred_skills,
                experience_level: parsedJobData.experience_level,
                domain: parsedJobData.domain
            },
            resume: {
                candidate_name: manualName || structuredData.candidate_name || 'Unknown',
                email: manualEmail || structuredData.email || '',
                phone: structuredData.phone || null,
                experience_years: structuredData.experience_years || null,
                skills: structuredData.skills || [],
                experience: structuredData.experience || [],
                education: structuredData.education || [],
                projects: structuredData.projects || [],
                social_profiles: socialProfiles,
                raw_text: this.uploadedResumeData.raw_text
            },
            custom_weights: customWeights
        };
    }

    parseJobDescription(jobText) {
        // Basic parsing of job description
        const lines = jobText.split('\n').map(line => line.trim()).filter(line => line);
        
        let title = 'Unknown Position';
        let company = 'Unknown Company';
        let domain = 'General';
        let experienceLevel = 'Mid Level';
        let requirements = [];
        let preferredSkills = [];
        
        // Try to extract title and company from first few lines
        if (lines.length > 0) {
            const firstLine = lines[0];
            // Look for patterns like "Senior Developer at Company" or "Company - Senior Developer"
            if (firstLine.includes(' at ')) {
                const parts = firstLine.split(' at ');
                title = parts[0].trim();
                company = parts[1].trim();
            } else if (firstLine.includes(' - ')) {
                const parts = firstLine.split(' - ');
                company = parts[0].trim();
                title = parts[1].trim();
            } else {
                title = firstLine;
            }
        }
        
        // Extract domain from title
        const titleLower = title.toLowerCase();
        if (titleLower.includes('frontend') || titleLower.includes('react') || titleLower.includes('vue')) {
            domain = 'Frontend Development';
        } else if (titleLower.includes('backend') || titleLower.includes('api') || titleLower.includes('server')) {
            domain = 'Backend Development';
        } else if (titleLower.includes('full stack') || titleLower.includes('fullstack')) {
            domain = 'Full Stack Development';
        } else if (titleLower.includes('data') || titleLower.includes('ml') || titleLower.includes('ai')) {
            domain = 'Data Science/ML';
        } else if (titleLower.includes('devops') || titleLower.includes('cloud')) {
            domain = 'DevOps/Cloud';
        } else if (titleLower.includes('mobile') || titleLower.includes('ios') || titleLower.includes('android')) {
            domain = 'Mobile Development';
        }
        
        // Extract experience level
        if (titleLower.includes('senior') || titleLower.includes('sr.')) {
            experienceLevel = 'Senior Level';
        } else if (titleLower.includes('lead') || titleLower.includes('principal') || titleLower.includes('staff')) {
            experienceLevel = 'Lead Level';
        } else if (titleLower.includes('junior') || titleLower.includes('jr.') || titleLower.includes('entry')) {
            experienceLevel = 'Entry Level';
        }
        
        // Extract requirements and skills (basic pattern matching)
        const jobTextLower = jobText.toLowerCase();
        const techKeywords = [
            'javascript', 'python', 'java', 'react', 'vue', 'angular', 'node.js', 'express',
            'django', 'flask', 'spring', 'html', 'css', 'typescript', 'go', 'rust',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'mongodb', 'postgresql',
            'mysql', 'redis', 'elasticsearch', 'git', 'ci/cd', 'tensorflow', 'pytorch'
        ];
        
        techKeywords.forEach(keyword => {
            if (jobTextLower.includes(keyword)) {
                requirements.push(keyword);
            }
        });
        
        return {
            title,
            company,
            domain,
            experience_level: experienceLevel,
            requirements: requirements.slice(0, 10), // Limit to 10 items
            preferred_skills: requirements.slice(0, 5) // Use first 5 requirements as preferred skills
        };
    }

    showProgressSection() {
        document.getElementById('inputForm').style.display = 'none';
        document.getElementById('analysisDashboard').classList.remove('hidden');
        
        const tasks = [
            { id: 'resume_jd_match', name: 'Resume and JD Matching' },
            { id: 'github_analyze', name: 'GitHub Analysis' },
            { id: 'linkedin_analyze', name: 'LinkedIn Analysis' },
            { id: 'twitter_analyze', name: 'Twitter Analysis' },
            { id: 'medium_analyze', name: 'Medium Analysis' },
            { id: 'project_evaluate', name: 'Project Evaluation' },
            { id: 'company_research', name: 'Company Research' },
            { id: 'final_score', name: 'Final Scoring' }
        ];

        const progressContainer = document.getElementById('progressTasks');
        progressContainer.innerHTML = '';

        tasks.forEach(task => {
            const taskElement = this.createTaskElement(task);
            progressContainer.appendChild(taskElement);
        });
        
        // Initialize thinking section
        this.updateThinkingContent('🚀 **Analysis Starting** - Initializing candidate evaluation process...');
    }

    createTaskElement(task) {
        const taskDiv = document.createElement('div');
        taskDiv.className = 'flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200';
        taskDiv.id = `task-${task.id}`;

        taskDiv.innerHTML = `
            <div class="flex items-center flex-1">
                <div class="task-status w-6 h-6 rounded-full bg-gray-300 flex items-center justify-center mr-3">
                    <span class="text-xs text-white">⏳</span>
                </div>
                <div class="flex-1">
                    <h4 class="font-medium text-sm">${task.name}</h4>
                    <p class="text-xs text-gray-500 task-message">Pending...</p>
                    <div class="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                        <div class="task-progress-bar bg-blue-600 h-1.5 rounded-full transition-all duration-300" style="width: 0%"></div>
                    </div>
                </div>
            </div>
            <div class="text-right ml-4">
                <div class="task-progress text-xs font-medium text-gray-600">0%</div>
            </div>
        `;

        return taskDiv;
    }

    connectWebSocket() {
        if (!this.currentAnalysisId) return;

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${this.currentAnalysisId}`;
        
        this.websocket = new WebSocket(wsUrl);

        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('WebSocket message:', data);
            
            if (data.type === 'progress_update') {
                this.updateProgress(data.progress);
                
                // Update thinking section with analysis content
                if (data.thinking_data) {
                    this.updateThinkingWithData(data.thinking_data);
                }
                
                if (data.final_analysis) {
                    this.showResults(data.final_analysis);
                }
            } else if (data.type === 'thinking_update') {
                // Handle the new thinking update format
                this.updateThinkingContent(data.content);
            } else if (data.type === 'final_analysis_stream') {
                // Handle streaming final analysis results
                this.updateFinalAnalysisStream(data.content, data.is_complete);
            }
        };

        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.websocket.onclose = () => {
            console.log('WebSocket connection closed');
        };
    }

    updateProgress(progressData) {
        progressData.forEach(task => {
            const taskElement = document.getElementById(`task-${task.task_id}`);
            if (!taskElement) return;

            const statusIcon = taskElement.querySelector('.task-status');
            const messageElement = taskElement.querySelector('.task-message');
            const progressElement = taskElement.querySelector('.task-progress');
            const progressBar = taskElement.querySelector('.task-progress-bar');

            messageElement.textContent = task.message || 'Processing...';
            const percentage = Math.round(task.progress_percentage);
            progressElement.textContent = `${percentage}%`;
            progressBar.style.width = `${percentage}%`;

            switch (task.status) {
                case 'pending':
                    statusIcon.className = 'task-status w-6 h-6 rounded-full bg-gray-300 flex items-center justify-center mr-3';
                    statusIcon.innerHTML = '<span class="text-xs text-white">⏳</span>';
                    progressBar.className = 'task-progress-bar bg-gray-400 h-1.5 rounded-full transition-all duration-300';
                    break;
                case 'in_progress':
                    statusIcon.className = 'task-status w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center mr-3 animate-pulse';
                    statusIcon.innerHTML = '<span class="text-xs text-white">🔄</span>';
                    progressBar.className = 'task-progress-bar bg-blue-500 h-1.5 rounded-full transition-all duration-300';
                    // Update thinking section when task starts
                    this.updateThinkingContent(`🔍 **${task.task_name}**: ${task.message}`);
                    break;
                case 'completed':
                    statusIcon.className = 'task-status w-6 h-6 rounded-full bg-green-500 flex items-center justify-center mr-3';
                    statusIcon.innerHTML = '<span class="text-xs text-white">✓</span>';
                    progressBar.className = 'task-progress-bar bg-green-500 h-1.5 rounded-full transition-all duration-300';
                    progressBar.style.width = '100%';
                    break;
                case 'failed':
                    statusIcon.className = 'task-status w-6 h-6 rounded-full bg-red-500 flex items-center justify-center mr-3';
                    statusIcon.innerHTML = '<span class="text-xs text-white">✗</span>';
                    progressBar.className = 'task-progress-bar bg-red-500 h-1.5 rounded-full transition-all duration-300';
                    break;
            }
        });
    }

    showResults(analysis) {
        document.getElementById('resultsSection').classList.remove('hidden');

        const resultsContent = document.getElementById('resultsContent');
        
        // Render markdown if available
        let detailedReport = analysis.detailed_report || 'No detailed report available';
        if (typeof marked !== 'undefined' && detailedReport) {
            try {
                detailedReport = marked.parse(detailedReport);
            } catch (e) {
                console.error('Markdown parsing error:', e);
                detailedReport = detailedReport.replace(/\n/g, '<br>');
            }
        } else {
            detailedReport = detailedReport.replace(/\n/g, '<br>');
        }
        
        resultsContent.innerHTML = `
            <div class="mb-8">
                <div class="text-center mb-6">
                    <div class="inline-flex items-center justify-center w-32 h-32 rounded-full ${this.getScoreColor(analysis.overall_score)} mb-4 shadow-lg">
                        <div class="text-center">
                            <div class="text-3xl font-bold text-white">${Math.round(analysis.overall_score)}%</div>
                            <div class="text-sm text-white opacity-90">Score</div>
                        </div>
                    </div>
                    <h3 class="text-4xl font-bold text-gray-800 mb-2">${analysis.recommendation}</h3>
                    <p class="text-xl text-gray-600">Overall Score: ${analysis.overall_score.toFixed(1)}/100</p>
                </div>
            </div>

            <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                <div class="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-lg border border-blue-200">
                    <h4 class="text-lg font-semibold mb-4 text-blue-800">Resume-JD Match</h4>
                    <div class="flex items-center justify-between">
                        <span class="text-blue-700">Score</span>
                        <span class="font-bold text-xl text-blue-800">${analysis.resume_jd_match_score}/100</span>
                    </div>
                </div>

                ${analysis.github_analysis ? `
                <div class="bg-gradient-to-br from-purple-50 to-purple-100 p-6 rounded-lg border border-purple-200">
                    <h4 class="text-lg font-semibold mb-4 text-purple-800">GitHub Analysis</h4>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between text-purple-700">
                            <span>Public Repos</span>
                            <span class="font-semibold">${analysis.github_analysis.public_repos_count}</span>
                        </div>
                        <div class="flex justify-between text-purple-700">
                            <span>Code Quality</span>
                            <span class="font-semibold">${analysis.github_analysis.code_quality_score.toFixed(1)}/100</span>
                        </div>
                        <div class="flex justify-between text-purple-700">
                            <span>Domain Relevance</span>
                            <span class="font-semibold">${analysis.github_analysis.domain_relevance_score.toFixed(1)}/100</span>
                        </div>
                    </div>
                </div>
                ` : ''}

                ${analysis.linkedin_analysis ? `
                <div class="bg-gradient-to-br from-indigo-50 to-indigo-100 p-6 rounded-lg border border-indigo-200">
                    <h4 class="text-lg font-semibold mb-4 text-indigo-800">LinkedIn Analysis</h4>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between text-indigo-700">
                            <span>Technical Posts</span>
                            <span class="font-semibold">${analysis.linkedin_analysis.technical_posts_count}</span>
                        </div>
                        <div class="flex justify-between text-indigo-700">
                            <span>Domain Relevance</span>
                            <span class="font-semibold">${analysis.linkedin_analysis.domain_relevance_score.toFixed(1)}/100</span>
                        </div>
                    </div>
                </div>
                ` : ''}

                ${analysis.medium_analysis ? `
                <div class="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-lg border border-green-200">
                    <h4 class="text-lg font-semibold mb-4 text-green-800">Medium Analysis</h4>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between text-green-700">
                            <span>Articles</span>
                            <span class="font-semibold">${analysis.medium_analysis.articles_count}</span>
                        </div>
                        <div class="flex justify-between text-green-700">
                            <span>Domain Relevant</span>
                            <span class="font-semibold">${analysis.medium_analysis.domain_relevant_articles}</span>
                        </div>
                        <div class="flex justify-between text-green-700">
                            <span>Domain Relevance</span>
                            <span class="font-semibold">${analysis.medium_analysis.domain_relevance_score.toFixed(1)}/100</span>
                        </div>
                    </div>
                </div>
                ` : ''}
            </div>

            <div class="mb-8">
                <h4 class="text-2xl font-semibold mb-6 text-gray-800">Comprehensive Analysis Report</h4>
                <div class="bg-gray-50 p-8 rounded-lg border border-gray-200 prose max-w-none">
                    ${detailedReport}
                </div>
            </div>

            <div class="text-center">
                <button onclick="location.reload()" 
                        class="bg-gradient-to-r from-secondary to-green-600 text-white py-4 px-8 rounded-lg font-semibold hover:from-green-600 hover:to-green-700 transition-all duration-200 shadow-lg transform hover:scale-105">
                    Start New Analysis
                </button>
            </div>
        `;
    }
    
    updateThinkingContent(content, append = true) {
        const thinkingContent = document.getElementById('thinkingContent');
        
        // If this is the first message, clear the placeholder and initialize
        if (thinkingContent.children.length === 1 && thinkingContent.children[0].textContent.includes('Waiting for analysis')) {
            thinkingContent.innerHTML = '<div id="thinkingMarkdown" class="prose max-w-none text-sm"></div>';
        }
        
        let markdownDiv = document.getElementById('thinkingMarkdown');
        if (!markdownDiv) {
            markdownDiv = document.createElement('div');
            markdownDiv.id = 'thinkingMarkdown';
            markdownDiv.className = 'prose max-w-none text-sm';
            thinkingContent.appendChild(markdownDiv);
        }
        
        // Add timestamp
        const timestamp = new Date().toLocaleTimeString();
        const timestampedContent = `**[${timestamp}]** ${content}`;
        
        if (append) {
            // Append to existing content
            const currentContent = markdownDiv.getAttribute('data-raw-content') || '';
            const newContent = currentContent + '\n\n' + timestampedContent;
            markdownDiv.setAttribute('data-raw-content', newContent);
            
            // Render markdown
            if (typeof marked !== 'undefined') {
                try {
                    markdownDiv.innerHTML = marked.parse(newContent);
                } catch (e) {
                    console.error('Markdown parsing error:', e);
                    markdownDiv.innerHTML = newContent.replace(/\n/g, '<br>');
                }
            } else {
                markdownDiv.innerHTML = newContent.replace(/\n/g, '<br>');
            }
        } else {
            // Replace content
            markdownDiv.setAttribute('data-raw-content', timestampedContent);
            if (typeof marked !== 'undefined') {
                try {
                    markdownDiv.innerHTML = marked.parse(timestampedContent);
                } catch (e) {
                    console.error('Markdown parsing error:', e);
                    markdownDiv.innerHTML = timestampedContent.replace(/\n/g, '<br>');
                }
            } else {
                markdownDiv.innerHTML = timestampedContent.replace(/\n/g, '<br>');
            }
        }
        
        thinkingContent.scrollTop = thinkingContent.scrollHeight;
    }
    
    updateThinkingWithData(thinkingData) {
        let content = '';
        
        if (thinkingData.resume_match) {
            content += `### Resume-JD Match Analysis\nAchieved **${thinkingData.resume_match.score}/100** compatibility score\n\n`;
        }
        
        if (thinkingData.github) {
            const gh = thinkingData.github;
            content += `### GitHub Analysis for @${gh.username}\n`;
            content += `- **Profile Stats:** ${gh.public_repos} repos, ${gh.followers} followers\n`;
            content += `- **Code Quality Score:** ${gh.code_quality_score}/100\n`;
            content += `- **Domain Relevance:** ${gh.domain_relevance}/100\n`;
            if (gh.top_repos && gh.top_repos.length > 0) {
                content += `- **Top Repositories:**\n`;
                gh.top_repos.forEach(repo => {
                    content += `  - **${repo.name}** (${repo.language || 'N/A'}) - ⭐${repo.stars} 🍴${repo.forks}\n`;
                });
            }
            content += '\n';
        }
        
        if (thinkingData.linkedin) {
            const li = thinkingData.linkedin;
            content += `### LinkedIn Analysis\n`;
            content += `- **Technical Posts:** ${li.technical_posts} total\n`;
            content += `- **Domain Relevant Posts:** ${li.domain_relevant_posts}\n`;
            content += `- **Domain Relevance Score:** ${li.domain_relevance}/100\n`;
            if (li.connections) content += `- **Connections:** ${li.connections}\n`;
            content += '\n';
        }
        
        if (thinkingData.twitter) {
            const tw = thinkingData.twitter;
            content += `### Twitter Analysis for @${tw.username}\n`;
            content += `- **Followers:** ${tw.followers}\n`;
            content += `- **Technical Tweets:** ${tw.technical_tweets}\n`;
            content += `- **Domain Relevant Tweets:** ${tw.domain_relevant_tweets}\n`;
            content += `- **Engagement Rate:** ${tw.engagement_rate}%\n`;
            content += `- **Domain Relevance Score:** ${tw.domain_relevance}/100\n\n`;
        }
        
        if (thinkingData.medium) {
            const md = thinkingData.medium;
            content += `### Medium Analysis for @${md.username}\n`;
            content += `- **Total Articles:** ${md.articles_count}\n`;
            content += `- **Domain Relevant Articles:** ${md.domain_relevant_articles}\n`;
            content += `- **Total Claps:** ${md.total_claps}\n`;
            content += `- **Followers:** ${md.followers}\n`;
            content += `- **Domain Relevance Score:** ${md.domain_relevance}/100\n\n`;
        }
        
        if (thinkingData.projects && thinkingData.projects.length > 0) {
            content += `### Project Analysis\nEvaluated **${thinkingData.projects.length}** projects:\n`;
            thinkingData.projects.forEach(p => {
                content += `- **${p.name}** ${p.is_live ? '🟢 Live' : '🔴 Not Live'}\n`;
                content += `  - Complexity: ${p.complexity_score}/100\n`;
                content += `  - Responsiveness: ${p.responsiveness_score}/100\n`;
                content += `  - SEO: ${p.seo_score}/100\n`;
                if (p.technologies && p.technologies.length > 0) {
                    content += `  - Technologies: ${p.technologies.join(', ')}\n`;
                }
            });
            content += '\n';
        }
        
        if (thinkingData.companies && thinkingData.companies.length > 0) {
            content += `### Company Research\nResearched **${thinkingData.companies.length}** companies:\n`;
            thinkingData.companies.forEach(c => {
                content += `- **${c.name}** (${c.tier})\n`;
                content += `  - Role: ${c.role}\n`;
                content += `  - Difficulty Score: ${c.difficulty_score}/100\n`;
                content += `  - Market Reputation: ${c.reputation}/100\n`;
            });
            content += '\n';
        }
        
        if (content) {
            this.updateThinkingContent(content.trim());
        }
    }

    updateFinalAnalysisStream(content, isComplete = false) {
        console.log('Streaming final analysis content:', content);
        
        // Show results section if not already visible
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection.classList.contains('hidden')) {
            resultsSection.classList.remove('hidden');
        }
        
        const resultsContent = document.getElementById('resultsContent');
        
        // Get or create streaming content div
        let streamingDiv = document.getElementById('streamingAnalysis');
        if (!streamingDiv) {
            streamingDiv = document.createElement('div');
            streamingDiv.id = 'streamingAnalysis';
            streamingDiv.className = 'prose max-w-none';
            resultsContent.innerHTML = '';
            resultsContent.appendChild(streamingDiv);
        }
        
        // Append new content
        const currentContent = streamingDiv.getAttribute('data-raw-content') || '';
        const newContent = currentContent + '\\n\\n' + content;
        streamingDiv.setAttribute('data-raw-content', newContent);
        
        // Render markdown if available
        if (typeof marked !== 'undefined') {
            try {
                streamingDiv.innerHTML = marked.parse(newContent);
            } catch (e) {
                console.error('Markdown parsing error:', e);
                streamingDiv.innerHTML = newContent.replace(/\\n/g, '<br>');
            }
        } else {
            streamingDiv.innerHTML = newContent.replace(/\\n/g, '<br>');
        }
        
        // Scroll to bottom to show new content
        streamingDiv.scrollTop = streamingDiv.scrollHeight;
        
        // Add completion indicator if done
        if (isComplete) {
            console.log('Final analysis streaming completed');
            const completionDiv = document.createElement('div');
            completionDiv.className = 'mt-8 text-center';
            completionDiv.innerHTML = `
                <div class=\"bg-green-50 border border-green-200 rounded-lg p-4 mb-4\">
                    <div class=\"flex items-center justify-center\">
                        <svg class=\"h-5 w-5 text-green-500 mr-2\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\">
                            <path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z\"></path>
                        </svg>
                        <p class=\"text-sm font-medium text-green-700\">Analysis Complete!</p>
                    </div>
                </div>
                <button onclick=\"location.reload()\" 
                        class=\"bg-gradient-to-r from-secondary to-green-600 text-white py-3 px-6 rounded-lg font-semibold hover:from-green-600 hover:to-green-700 transition-all duration-200 shadow-lg transform hover:scale-105\">
                    Start New Analysis
                </button>
            `;
            resultsContent.appendChild(completionDiv);
        }
    }

    getScoreColor(score) {
        if (score >= 85) return 'bg-green-500';
        if (score >= 70) return 'bg-blue-500';
        if (score >= 55) return 'bg-yellow-500';
        return 'bg-red-500';
    }
}

// Global function for collapsible sections
function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    const chevronId = sectionId.replace('Collapse', 'Chevron');
    const chevron = document.getElementById(chevronId);
    
    if (section.classList.contains('hidden')) {
        section.classList.remove('hidden');
        chevron.style.transform = 'rotate(0deg)';
    } else {
        section.classList.add('hidden');
        chevron.style.transform = 'rotate(-90deg)';
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing app...');
    const app = new HiringAgentApp();
    
    // Debug: Check if elements exist
    setTimeout(() => {
        const uploadArea = document.getElementById('resumeUploadArea');
        const fileInput = document.getElementById('resumeFileInput');
        const chooseBtn = document.getElementById('chooseFileBtn');
        
        console.log('Debug - Elements after init:', {
            uploadArea: !!uploadArea,
            fileInput: !!fileInput,
            chooseBtn: !!chooseBtn
        });
        
        if (chooseBtn) {
            console.log('Choose button found, adding test click listener');
            chooseBtn.addEventListener('click', () => {
                console.log('TEST: Choose button clicked directly');
            });
        }
    }, 100);
});
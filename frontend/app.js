class HiringAgentApp {
    constructor() {
        this.currentAnalysisId = null;
        this.websocket = null;
        this.uploadedResumeData = null;
        this.parsedJobData = null;
        this.sseStreamStarted = false;
        this.initializeEventListeners();
        this.initializeSliders();
        this.initializeFileUpload();
        this.initializeWeightModes();
    }

    initializeEventListeners() {
        document.getElementById('startAnalysis').addEventListener('click', () => this.startAnalysis());
        
        // Only add change file button listener if it exists
        const changeFileBtn = document.getElementById('changeFileBtn');
        if (changeFileBtn) {
            changeFileBtn.addEventListener('click', () => this.resetFileUpload());
        }
    }

    async initializeSliders() {
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

        // Fetch and populate weight values from backend
        try {
            const response = await fetch('/api/weights');
            if (response.ok) {
                const weights = await response.json();
                this.populateWeights(weights.default_weights);
            }
        } catch (error) {
            console.error('Failed to fetch weights from backend:', error);
        }
    }

    populateWeights(weights) {
        const weightMapping = {
            'resumeJdMatch': 'resume_jd_match',
            'githubAnalysis': 'github_analysis', 
            'linkedinAnalysis': 'linkedin_analysis',
            'technicalBlogs': 'technical_blogs',
            'projectQuality': 'project_quality',
            'workExperience': 'work_experience'
        };

        Object.entries(weightMapping).forEach(([sliderId, weightKey]) => {
            const slider = document.getElementById(sliderId);
            const valueSpan = document.getElementById(sliderId + 'Value');
            
            if (slider && valueSpan && weights[weightKey] !== undefined) {
                const value = weights[weightKey];
                slider.value = value;
                valueSpan.textContent = value;
            }
        });
    }

    initializeFileUpload() {
        const fileInput = document.getElementById('resumeFileInput');
        const dragDropArea = document.getElementById('dragDropArea');
        
        if (!fileInput) {
            return;
        }
        
        // File input change - this is the main functionality
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                const file = e.target.files[0];
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

    async initializeWeightModes() {
        // Add click listeners for weight mode cards
        const professionalMode = document.getElementById('professionalMode');
        const fresherMode = document.getElementById('fresherMode');
        const professionalRadio = document.getElementById('professionalModeRadio');
        const fresherRadio = document.getElementById('fresherModeRadio');

        // Make the entire card clickable
        professionalMode.addEventListener('click', () => {
            professionalRadio.checked = true;
            this.updateWeightModeUI();
            this.loadWeightModeValues('professional');
        });

        fresherMode.addEventListener('click', () => {
            fresherRadio.checked = true;
            this.updateWeightModeUI();
            this.loadWeightModeValues('fresher');
        });

        // Also listen to radio button changes
        professionalRadio.addEventListener('change', () => {
            if (professionalRadio.checked) {
                this.updateWeightModeUI();
                this.loadWeightModeValues('professional');
            }
        });

        fresherRadio.addEventListener('change', () => {
            if (fresherRadio.checked) {
                this.updateWeightModeUI();
                this.loadWeightModeValues('fresher');
            }
        });

        // Initialize with default mode
        this.updateWeightModeUI();
        this.loadWeightModeValues('professional');
    }

    updateWeightModeUI() {
        const professionalMode = document.getElementById('professionalMode');
        const fresherMode = document.getElementById('fresherMode');
        const professionalRadio = document.getElementById('professionalModeRadio');
        const fresherRadio = document.getElementById('fresherModeRadio');

        // Remove active styles from both
        professionalMode.classList.remove('border-primary', 'bg-blue-50');
        fresherMode.classList.remove('border-primary', 'bg-blue-50');

        // Add active styles to selected mode
        if (professionalRadio.checked) {
            professionalMode.classList.add('border-primary', 'bg-blue-50');
        } else if (fresherRadio.checked) {
            fresherMode.classList.add('border-primary', 'bg-blue-50');
        }
    }

    async loadWeightModeValues(mode) {
        try {
            const response = await fetch(`/api/weights/mode/${mode}`);
            if (response.ok) {
                const modeData = await response.json();
                this.populateWeights(modeData.weights);
            }
        } catch (error) {
            console.error('Failed to load weight mode values:', error);
        }
    }

    getSelectedWeightMode() {
        const professionalRadio = document.getElementById('professionalModeRadio');
        return professionalRadio.checked ? 'professional' : 'fresher';
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
            
            // Note: SSE stream will be started when analysis is near completion
            
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
            weight_mode: this.getSelectedWeightMode(),
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
            { id: 'resume_jd_match', name: 'Resume-JD Match', icon: 'document-text', tooltip: 'Analyzing resume compatibility with job requirements' },
            { id: 'github_analyze', name: 'GitHub', icon: 'code', tooltip: 'Evaluating GitHub repositories and code quality' },
            { id: 'linkedin_analyze', name: 'LinkedIn', icon: 'briefcase', tooltip: 'Analyzing professional LinkedIn profile' },
            { id: 'twitter_analyze', name: 'Twitter', icon: 'chat', tooltip: 'Reviewing Twitter technical discussions' },
            { id: 'medium_analyze', name: 'Medium', icon: 'pencil', tooltip: 'Evaluating Medium articles and technical writing' },
            { id: 'project_evaluate', name: 'Projects', icon: 'globe', tooltip: 'Analyzing live projects and portfolio quality' },
            { id: 'company_research', name: 'Companies', icon: 'office-building', tooltip: 'Researching work experience and company difficulty' },
            { id: 'final_score', name: 'Final Score', icon: 'chart-bar', tooltip: 'Calculating overall candidate score and recommendation' }
        ];

        const progressContainer = document.getElementById('analysisProgress');
        progressContainer.innerHTML = '';

        tasks.forEach(task => {
            const taskElement = this.createCircularProgressElement(task);
            progressContainer.appendChild(taskElement);
        });
        
        // Initialize thinking section
        this.updateThinkingContent('🚀 **Analysis Starting** - Initializing candidate evaluation process...');
    }

    createCircularProgressElement(task) {
        const progressDiv = document.createElement('div');
        progressDiv.className = 'relative';
        progressDiv.id = `task-${task.id}`;

        progressDiv.innerHTML = `
            <div class="circular-progress">
                <div class="tooltip">${task.tooltip}</div>
                <svg class="progress-ring" width="80" height="80">
                    <circle
                        class="progress-ring__background"
                        stroke="#e5e7eb"
                        stroke-width="4"
                        fill="transparent"
                        r="36"
                        cx="40"
                        cy="40"/>
                    <circle
                        class="progress-ring__circle progress-ring__progress"
                        stroke="#3b82f6"
                        stroke-width="4"
                        fill="transparent"
                        r="36"
                        cx="40"
                        cy="40"
                        style="stroke-dashoffset: 251.2;"/>
                </svg>
                <div class="progress-content">
                    <div class="progress-icon">
                        ${this.getIconSVG(task.icon)}
                    </div>
                    <div class="progress-percentage">0%</div>
                </div>
            </div>
            <div class="analysis-label">${task.name}</div>
        `;

        return progressDiv;
    }

    connectWebSocket() {
        if (!this.currentAnalysisId) return;

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${this.currentAnalysisId}`;
        
        this.websocket = new WebSocket(wsUrl);

        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'progress_update') {
                this.updateProgress(data.progress);
                
                // Check if analysis is near completion to start SSE stream
                const completedTasks = data.progress.filter(task => task.status === 'completed').length;
                const totalTasks = data.progress.length;
                
                // Start SSE stream when most tasks are completed (6 out of 7+ tasks)
                if (completedTasks >= 6 && !this.sseStreamStarted) {
                    this.sseStreamStarted = true;
                    this.startSSEStream(this.currentAnalysisId);
                }
                
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
            // Handle WebSocket error silently
        };

        this.websocket.onclose = () => {
            // Handle WebSocket close silently
        };
    }

    updateProgress(progressData) {
        progressData.forEach(task => {
            const taskElement = document.getElementById(`task-${task.task_id}`);
            if (!taskElement) return;

            const progressRing = taskElement.querySelector('.progress-ring__progress');
            const progressIcon = taskElement.querySelector('.progress-icon');
            const progressPercentage = taskElement.querySelector('.progress-percentage');
            const circularProgress = taskElement.querySelector('.circular-progress');

            // Use score if available and task is completed, otherwise show progress percentage
            let displayValue, circularValue;
            const statusValue = task.status.value || task.status;
            
            if (statusValue === 'completed' && task.score !== null && task.score !== undefined) {
                displayValue = Math.round(task.score);
                circularValue = task.score;
                progressPercentage.textContent = `${displayValue}`;
                // Debugging: Log when we're showing a score
                if (window.location.search.includes('debug')) {
                    console.log(`Showing score for ${task.task_id}: ${task.score}`);
                }
            } else {
                displayValue = Math.round(task.progress_percentage || 0);
                circularValue = task.progress_percentage || 0;
                progressPercentage.textContent = statusValue === 'pending' ? '--' : `${displayValue}%`;
            }

            // Calculate stroke-dashoffset for circular progress
            const circumference = 2 * Math.PI * 36; // r=36
            const offset = circumference - (circularValue / 100) * circumference;
            progressRing.style.strokeDashoffset = offset;

            // Remove any existing status classes
            progressRing.classList.remove('completed', 'failed');
            progressIcon.classList.remove('completed', 'failed', 'pulse-progress');
            circularProgress.classList.remove('pulse-progress');
            switch (statusValue) {
                case 'pending':
                    progressRing.style.stroke = '#9ca3af';
                    break;
                case 'in_progress':
                    progressRing.style.stroke = '#3b82f6';
                    circularProgress.classList.add('pulse-progress');
                    // Update thinking section when task starts
                    this.updateThinkingContent(`🔍 **${task.task_name}**: ${task.message}`);
                    break;
                case 'completed':
                    progressRing.classList.add('completed');
                    progressIcon.classList.add('completed');
                    
                    // Color code based on score if available
                    if (task.score !== null && task.score !== undefined) {
                        if (task.score >= 85) {
                            progressRing.style.stroke = '#10b981'; // Green for excellent
                        } else if (task.score >= 70) {
                            progressRing.style.stroke = '#3b82f6'; // Blue for good
                        } else if (task.score >= 55) {
                            progressRing.style.stroke = '#f59e0b'; // Yellow for average
                        } else {
                            progressRing.style.stroke = '#ef4444'; // Red for poor
                        }
                    } else {
                        progressRing.style.stroke = '#10b981'; // Default green
                    }
                    
                    // Don't override other calculated values
                    break;
                case 'failed':
                    progressRing.classList.add('failed');
                    progressIcon.classList.add('failed');
                    progressRing.style.stroke = '#ef4444';
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
        const newContent = currentContent + '\n\n' + content;
        streamingDiv.setAttribute('data-raw-content', newContent);
        
        // Render markdown if available
        if (typeof marked !== 'undefined') {
            try {
                streamingDiv.innerHTML = marked.parse(newContent);
            } catch (e) {
                console.error('Markdown parsing error:', e);
                streamingDiv.innerHTML = newContent.replace(/\n/g, '<br>');
            }
        } else {
            streamingDiv.innerHTML = newContent.replace(/\n/g, '<br>');
        }
        
        // Scroll to bottom to show new content
        streamingDiv.scrollTop = streamingDiv.scrollHeight;
        
        // Add completion indicator if done
        if (isComplete) {
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

    startSSEStream(analysisId) {
        // Show results section immediately for streaming
        const resultsSection = document.getElementById('resultsSection');
        resultsSection.classList.remove('hidden');
        
        // Setup chatbot-style container
        const resultsContent = document.getElementById('resultsContent');
        resultsContent.innerHTML = `
            <div class="bg-white rounded-lg shadow-lg p-6">
                <div class="flex items-center mb-6">
                    <div class="w-10 h-10 bg-gradient-to-r from-secondary to-green-600 rounded-full flex items-center justify-center mr-4">
                        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a9 9 0 117.072 0l-.548.547A3.374 3.374 0 0014.846 21H9.154a3.374 3.374 0 00-2.692-1.244l-.548-.547z"></path>
                        </svg>
                    </div>
                    <div>
                        <h3 class="text-xl font-bold text-gray-800">AI Analysis Assistant</h3>
                        <p class="text-gray-600">Generating comprehensive candidate evaluation...</p>
                    </div>
                </div>
                <div id="chatContainer" class="space-y-4 max-h-96 overflow-y-auto">
                    <div class="flex items-start space-x-3">
                        <div class="w-8 h-8 bg-secondary rounded-full flex items-center justify-center flex-shrink-0">
                            <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                            </svg>
                        </div>
                        <div class="bg-gray-100 rounded-lg p-4 max-w-full">
                            <div id="streamingContent" class="prose prose-sm max-w-none"></div>
                            <div id="typingIndicator" class="flex items-center mt-2">
                                <div class="flex space-x-1">
                                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                                </div>
                                <span class="ml-2 text-sm text-gray-500">Analyzing...</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Setup EventSource for SSE
        const eventSource = new EventSource(`/api/analysis/${analysisId}/stream`);
        let accumulatedContent = '';
        let hasReceivedData = false;
        
        // Set up timeout for SSE connection (2 minutes)
        const timeout = setTimeout(() => {
            if (!hasReceivedData) {
                console.warn('SSE connection timeout - no data received');
                this.handleSSEError('Connection timeout - analysis taking too long');
                eventSource.close();
            }
        }, 120000); // 2 minutes
        
        eventSource.onmessage = (event) => {
            try {
                hasReceivedData = true;
                clearTimeout(timeout);
                
                const data = JSON.parse(event.data);
                
                if (data.error) {
                    this.handleSSEError(data.error);
                    eventSource.close();
                    return;
                }
                
                if (data.type === 'message') {
                    accumulatedContent += data.content;
                    this.updateStreamingContent(accumulatedContent);
                    
                    if (data.is_complete) {
                        this.hideTypingIndicator();
                        this.showCompletionMessage();
                        eventSource.close();
                    }
                }
                
            } catch (error) {
                console.error('Error parsing SSE data:', error);
            }
        };
        
        eventSource.onerror = (error) => {
            console.error('SSE error:', error);
            clearTimeout(timeout);
            this.handleSSEError('Connection error occurred');
            eventSource.close();
        };
        
        // Store for cleanup
        this.currentEventSource = eventSource;
    }
    
    updateStreamingContent(content) {
        const streamingDiv = document.getElementById('streamingContent');
        if (streamingDiv) {
            // Render markdown if available
            if (typeof marked !== 'undefined') {
                try {
                    streamingDiv.innerHTML = marked.parse(content);
                } catch (e) {
                    console.error('Markdown parsing error:', e);
                    streamingDiv.innerHTML = content.replace(/\n/g, '<br>');
                }
            } else {
                streamingDiv.innerHTML = content.replace(/\n/g, '<br>');
            }
            
            // Auto-scroll to bottom
            const chatContainer = document.getElementById('chatContainer');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }
    }
    
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.style.display = 'none';
        }
    }
    
    showCompletionMessage() {
        const chatContainer = document.getElementById('chatContainer');
        if (chatContainer) {
            const completionDiv = document.createElement('div');
            completionDiv.className = 'flex justify-center mt-6';
            completionDiv.innerHTML = `
                <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div class="flex items-center">
                        <svg class="h-5 w-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        <p class="text-sm font-medium text-green-700">Analysis Complete!</p>
                    </div>
                    <button onclick="location.reload()" 
                            class="mt-3 bg-gradient-to-r from-secondary to-green-600 text-white py-2 px-4 rounded-lg font-semibold hover:from-green-600 hover:to-green-700 transition-all duration-200 shadow-lg text-sm">
                        Start New Analysis
                    </button>
                </div>
            `;
            chatContainer.appendChild(completionDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }
    
    handleSSEError(errorMessage) {
        const streamingDiv = document.getElementById('streamingContent');
        if (streamingDiv) {
            streamingDiv.innerHTML = `
                <div class="bg-red-50 border border-red-200 rounded p-3">
                    <h4 class="text-red-800 font-semibold">Analysis Error</h4>
                    <p class="text-red-700 text-sm mt-1">${errorMessage}</p>
                    <button onclick="location.reload()" 
                            class="mt-2 bg-red-600 text-white py-1 px-3 rounded text-sm hover:bg-red-700">
                        Try Again
                    </button>
                </div>
            `;
        }
        this.hideTypingIndicator();
    }

    getScoreColor(score) {
        if (score >= 85) return 'bg-green-500';
        if (score >= 70) return 'bg-blue-500';
        if (score >= 55) return 'bg-yellow-500';
        return 'bg-red-500';
    }

    // Helper method to get SVG icons
    getIconSVG(iconName) {
        const icons = {
            'document-text': `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="24" height="24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>`,
            'code': `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="24" height="24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path>
            </svg>`,
            'briefcase': `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="24" height="24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2-2v2m8 0H8m8 0v2a2 2 0 01-2 2H10a2 2 0 01-2-2V6"></path>
            </svg>`,
            'chat': `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="24" height="24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
            </svg>`,
            'pencil': `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="24" height="24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path>
            </svg>`,
            'globe': `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="24" height="24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"></path>
            </svg>`,
            'office-building': `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="24" height="24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2-2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
            </svg>`,
            'chart-bar': `<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" width="24" height="24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
            </svg>`
        };
        return icons[iconName] || icons['document-text'];
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
    const app = new HiringAgentApp();
});
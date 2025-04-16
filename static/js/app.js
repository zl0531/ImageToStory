document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const fileInput = document.getElementById('file-input');
    const dropzone = document.getElementById('dropzone');
    const previewContainer = document.getElementById('preview-container');
    const imagePreview = document.getElementById('image-preview');
    const changeImageBtn = document.getElementById('change-image');
    const generateBtn = document.getElementById('generate-btn');
    
    const initialMessage = document.getElementById('initial-message');
    const loadingElement = document.getElementById('loading');
    const storyContainer = document.getElementById('story-container');
    const storyContent = document.getElementById('story-content');
    const analysisContent = document.getElementById('analysis-content');
    const errorContainer = document.getElementById('error-container');
    const errorMessage = document.getElementById('error-message');
    
    const regenerateBtn = document.getElementById('regenerate-btn');
    const customRegenerateBtn = document.getElementById('custom-regenerate-btn');
    const promptInput = document.getElementById('prompt-input');
    const downloadBtn = document.getElementById('download-btn');
    const copyBtn = document.getElementById('copy-btn');
    
    // Current file to upload
    let currentFile = null;
    // Current story and analysis text
    let currentStory = '';
    let currentAnalysis = '';
    
    // ===== File handling =====
    
    // Setup the click handler for the dropzone
    dropzone.addEventListener('click', function() {
        fileInput.click();
    });
    
    // Handle file selection
    fileInput.addEventListener('change', function(e) {
        handleFileSelect(e.target.files[0]);
    });
    
    // Drag and drop events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, function() {
            dropzone.classList.add('dragover');
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, function() {
            dropzone.classList.remove('dragover');
        }, false);
    });
    
    dropzone.addEventListener('drop', function(e) {
        const dt = e.dataTransfer;
        const file = dt.files[0];
        handleFileSelect(file);
    }, false);
    
    // Change image button
    changeImageBtn.addEventListener('click', function() {
        resetUI();
    });
    
    // Handle file selection
    function handleFileSelect(file) {
        // Validate file type
        const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
        if (!file || !validTypes.includes(file.type)) {
            showError('Please select a valid image file (JPEG, PNG, or GIF)');
            return;
        }
        
        currentFile = file;
        
        // Show preview
        const reader = new FileReader();
        reader.onload = function(e) {
            imagePreview.src = e.target.result;
            dropzone.classList.add('d-none');
            previewContainer.classList.remove('d-none');
            generateBtn.disabled = false;
            
            // Hide any previous results
            initialMessage.classList.remove('d-none');
            storyContainer.classList.add('d-none');
            errorContainer.classList.add('d-none');
        };
        reader.readAsDataURL(file);
    }
    
    // ===== Story Generation =====
    
    // Generate story button
    generateBtn.addEventListener('click', function() {
        if (!currentFile) {
            showError('Please select an image first');
            return;
        }
        
        generateStory();
    });
    
    // Regenerate story button
    regenerateBtn.addEventListener('click', function() {
        regenerateStory();
    });
    
    // Custom regenerate button
    customRegenerateBtn.addEventListener('click', function() {
        regenerateStory(promptInput.value);
    });
    
    // Generate story from uploaded image
    function generateStory() {
        // Show loading state
        initialMessage.classList.add('d-none');
        loadingElement.classList.remove('d-none');
        storyContainer.classList.add('d-none');
        errorContainer.classList.add('d-none');
        
        // Create form data
        const formData = new FormData();
        formData.append('image', currentFile);
        
        // Send request to server
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            loadingElement.classList.add('d-none');
            
            if (data.success) {
                // Store current story and analysis
                currentStory = data.story;
                currentAnalysis = data.imageAnalysis;
                
                // Display the results
                storyContent.innerHTML = formatStoryText(data.story);
                analysisContent.textContent = data.imageAnalysis;
                storyContainer.classList.remove('d-none');
            } else {
                showError(data.error || 'An error occurred while generating the story');
            }
        })
        .catch(error => {
            loadingElement.classList.add('d-none');
            showError('Network error. Please try again later.');
            console.error('Error:', error);
        });
    }
    
    // Regenerate story with optional custom prompt
    function regenerateStory(customPrompt = '') {
        // Show loading state
        loadingElement.classList.remove('d-none');
        storyContainer.classList.add('d-none');
        errorContainer.classList.add('d-none');
        
        // Send request to server
        fetch('/regenerate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: customPrompt
            })
        })
        .then(response => response.json())
        .then(data => {
            loadingElement.classList.add('d-none');
            
            if (data.success) {
                // Update current story
                currentStory = data.story;
                
                // Display the results
                storyContent.innerHTML = formatStoryText(data.story);
                storyContainer.classList.remove('d-none');
            } else {
                showError(data.error || 'An error occurred while regenerating the story');
            }
        })
        .catch(error => {
            loadingElement.classList.add('d-none');
            showError('Network error. Please try again later.');
            console.error('Error:', error);
        });
    }
    
    // ===== Utility Functions =====
    
    // Format story text with paragraphs
    function formatStoryText(text) {
        // Replace newlines with HTML paragraphs
        return text.split('\n').filter(p => p.trim() !== '').map(p => 
            `<p>${p}</p>`
        ).join('');
    }
    
    // Show error message
    function showError(message) {
        errorMessage.textContent = message;
        errorContainer.classList.remove('d-none');
        loadingElement.classList.add('d-none');
    }
    
    // Reset UI to initial state
    function resetUI() {
        // Reset file selection
        fileInput.value = '';
        currentFile = null;
        
        // Reset UI elements
        dropzone.classList.remove('d-none');
        previewContainer.classList.add('d-none');
        generateBtn.disabled = true;
        
        // Reset results
        initialMessage.classList.remove('d-none');
        storyContainer.classList.add('d-none');
        errorContainer.classList.add('d-none');
        
        // Clear custom prompt
        promptInput.value = '';
    }
    
    // ===== Download and Copy Functions =====
    
    // Download story as text file
    downloadBtn.addEventListener('click', function() {
        if (!currentStory) return;
        
        const blob = new Blob([currentStory], {type: 'text/plain'});
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = 'generated-story.txt';
        document.body.appendChild(a);
        a.click();
        
        // Cleanup
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }, 100);
    });
    
    // Copy story to clipboard
    copyBtn.addEventListener('click', function() {
        if (!currentStory) return;
        
        navigator.clipboard.writeText(currentStory).then(
            function() {
                // Show success tooltip or notification
                const originalText = copyBtn.innerHTML;
                copyBtn.innerHTML = '<i class="fas fa-check me-2"></i>Copied!';
                
                setTimeout(() => {
                    copyBtn.innerHTML = originalText;
                }, 2000);
            },
            function() {
                showError('Failed to copy text to clipboard');
            }
        );
    });
});

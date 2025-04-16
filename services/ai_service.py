import os
import json
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Initialize Google Generative AI (Gemini) client
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Configure Gemini models
IMAGE_MODEL = "gemini-2.0-flash"  # Gemini's multimodal model for image processing
TEXT_MODEL = "gemini-2.0-flash"  # Gemini's model for text generation

def analyze_image(base64_image, language="en"):
    """
    Analyze an image using Google's Gemini Flash capabilities.

    Args:
        base64_image: Base64 encoded image
        language: Language code ('en' for English, 'zh' for Chinese)

    Returns:
        String containing analysis of the image
    """
    try:
        # Log the start of image analysis and API key status
        logger.info(f"Starting image analysis with model {IMAGE_MODEL}")
        logger.info(f"API Key configured: {bool(GOOGLE_API_KEY)}")

        # Log image size to help diagnose memory issues
        image_size_kb = len(base64_image) / 1024
        logger.info(f"Processing image of size: {image_size_kb:.2f} KB")

        if image_size_kb > 1000:
            logger.warning(f"Large image detected ({image_size_kb:.2f} KB). This may cause memory issues.")

        # Initialize the model
        logger.info("Initializing Gemini model")
        model = genai.GenerativeModel(IMAGE_MODEL)

        image_parts = [
            {
                "mime_type": "image/jpeg",
                "data": base64_image
            }
        ]

        # Dynamic prompt based on language
        logger.info(f"Using language: {language}")
        if language == "zh":
            prompt = """
            详细分析这张图片。识别关键元素、场景设置、人物、活动、情感、颜色以及任何值得注意或有趣的方面。
            提供一个全面的描述，可以用于创意讲故事。请使用中文回答。
            """
        else:
            prompt = """
            Analyze this image in detail. Identify the key elements, settings, people,
            activities, emotions, colors, and any notable or interesting aspects.
            Provide a comprehensive description that could be used for creative storytelling.
            """

        # Log before API call
        logger.info("Sending request to Gemini API")
        try:
            response = model.generate_content([prompt, image_parts[0]])
            logger.info("Successfully received response from Gemini API")
            return response.text
        except Exception as api_error:
            logger.error(f"Gemini API error: {str(api_error)}", exc_info=True)
            # Re-raise with more context
            raise Exception(f"Gemini API error: {str(api_error)}")

    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}", exc_info=True)
        raise Exception(f"Failed to analyze the image: {str(e)}")

def generate_story(image_analysis, custom_prompt="", language="en"):
    """
    Generate a creative story based on image analysis using Google's Gemini.

    Args:
        image_analysis: Text description of the image
        custom_prompt: Optional custom instructions for the story
        language: Language code ('en' for English, 'zh' for Chinese)

    Returns:
        String containing the generated story
    """
    try:
        # Log the start of story generation
        logger.info(f"Starting story generation with model {TEXT_MODEL}")
        logger.info(f"Using language: {language}, Custom prompt: {bool(custom_prompt)}")

        # Log the length of the image analysis
        analysis_length = len(image_analysis) if image_analysis else 0
        logger.info(f"Image analysis length: {analysis_length} characters")

        # Initialize the model
        logger.info("Initializing Gemini model for story generation")
        model = genai.GenerativeModel(TEXT_MODEL)

        # Prepare the prompt based on language
        if language == "zh":
            system_prompt = """
            你是一位专业的创意作家，擅长根据图像描述生成引人入胜的故事。
            创作生动的叙述，包含引人入胜的角色和有趣的情节。请使用中文回答。
            """

            prompt = f"""
            根据以下图像分析，创作一个引人入胜、富有创意且结构完整的短篇故事（约300-500字）。
            故事应该有清晰的开头、中间和结尾，包含有趣的角色和叙事。

            图像分析: {image_analysis}
            """

            # Add custom prompt if provided
            if custom_prompt:
                prompt += f"\n\n故事的额外指示: {custom_prompt}"
                logger.info("Added custom prompt in Chinese")
        else:
            system_prompt = """
            You are a creative writer specializing in generating engaging stories from image descriptions.
            Create vivid narratives with compelling characters and interesting plots.
            """

            prompt = f"""
            Based on the following image analysis, create an engaging, creative, and
            well-structured short story (around 300-500 words). The story should have
            a clear beginning, middle, and end, with interesting characters and narrative.

            Image analysis: {image_analysis}
            """

            # Add custom prompt if provided
            if custom_prompt:
                prompt += f"\n\nAdditional instructions for the story: {custom_prompt}"
                logger.info("Added custom prompt in English")

        # Configure the generation settings
        logger.info("Configuring generation settings")
        generation_config = {
            "temperature": 0.9,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1000,
        }

        # Create a chat session for better context handling
        logger.info("Creating chat session")
        chat = model.start_chat(history=[
            {"role": "user", "parts": [system_prompt]},
        ])

        # Send the message and get the response
        logger.info("Sending message to Gemini API for story generation")
        try:
            response = chat.send_message(prompt)
            logger.info("Successfully received story from Gemini API")
            return response.text
        except Exception as api_error:
            logger.error(f"Gemini API error during story generation: {str(api_error)}", exc_info=True)
            raise Exception(f"Gemini API error during story generation: {str(api_error)}")

    except Exception as e:
        logger.error(f"Error generating story: {str(e)}", exc_info=True)
        raise Exception(f"Failed to generate a story: {str(e)}")

def analyze_image_and_generate_story(base64_image, custom_prompt="", language="en"):
    """
    Analyze an image and generate a story based on the analysis.

    Args:
        base64_image: Base64 encoded image
        custom_prompt: Optional custom prompt for the story
        language: Language code ('en' for English, 'zh' for Chinese)

    Returns:
        Tuple containing (image_analysis, story)
    """
    image_analysis = analyze_image(base64_image, language)
    story = generate_story(image_analysis, custom_prompt, language)
    return image_analysis, story

def regenerate_story(base64_image, custom_prompt="", language="en"):
    """
    Regenerate a story for an already analyzed image with optional custom prompt.

    Args:
        base64_image: Base64 encoded image
        custom_prompt: Optional custom prompt for the story
        language: Language code ('en' for English, 'zh' for Chinese)

    Returns:
        String containing the regenerated story
    """
    # Re-analyze the image to get fresh inspiration
    image_analysis = analyze_image(base64_image, language)
    return generate_story(image_analysis, custom_prompt, language)


import os
import base64
import io
import json
import numpy as np
from PIL import Image, ImageDraw

try:
    from google import genai
    from google.genai import types
    IS_GEMINI_AVAILABLE = True
except ImportError:
    IS_GEMINI_AVAILABLE = False

def set_gemini_api_key():
    os.environ['GEMINI_API_KEY'] = 'AIzaSyCwnu6op6-gwG21kW61RIJ-KJziVoouagg'

def get_gemini_client():
    if not IS_GEMINI_AVAILABLE:
        return None
    
    try:
        genai.configure(api_key=os.environ['GEMINI_API_KEY'])
        client = genai.Client()
        return client
    except Exception as e:
        print(f"Error creating Gemini client: {e}")
        return None

def parse_json(json_output: str):
  # Parsing out the markdown fencing
  lines = json_output.splitlines()
  for i, line in enumerate(lines):
    if line == "```json":
      json_output = "\n".join(lines[i+1:])  # Remove everything before "```json"
      output = json_output.split("```")[0]  # Remove everything after the closing "```"
      break  # Exit the loop once "```json" is found
  return json_output

def extract_segmentation_masks(image_path: str, output_dir: str = "segmentation_outputs"):
  client = get_gemini_client()
  if not client:
      return

  # Load and resize image
  im = Image.open(image_path)
  im.thumbnail([1024, 1024], Image.Resampling.LANCZOS)

  prompt = """
  Give the segmentation masks for the wooden and glass items.
  Output a JSON list of segmentation masks where each entry contains the 2D
  bounding box in the key "box_2d", the segmentation mask in key "mask", and
  the text label in the key "label". Use descriptive labels.
  """

  config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_budget=0) # set thinking_budget to 0 for better results in object detection
  )

  response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[prompt, im], # Pillow images can be directly passed as inputs (which will be converted by the SDK)
    config=config
  )

  # Parse JSON response
  items = json.loads(parse_json(response.text))

  # Create output directory
  os.makedirs(output_dir, exist_ok=True)

  # Process each mask
  for i, item in enumerate(items):
      # Get bounding box coordinates
      box = item["box_2d"]
      y0 = int(box[0] / 1000 * im.size[1])
      x0 = int(box[1] / 1000 * im.size[0])
      y1 = int(box[2] / 1000 * im.size[1])
      x1 = int(box[3] / 1000 * im.size[0])

      # Skip invalid boxes
      if y0 >= y1 or x0 >= x1:
          continue

      # Process mask
      png_str = item["mask"]
      if not png_str.startswith("data:image/png;base64,"):
          continue

      # Remove prefix
      png_str = png_str.removeprefix("data:image/png;base64,")
      mask_data = base64.b64decode(png_str)
      mask = Image.open(io.BytesIO(mask_data))

      # Resize mask to match bounding box
      mask = mask.resize((x1 - x0, y1 - y0), Image.Resampling.BILINEAR)

      # Convert mask to numpy array for processing
      mask_array = np.array(mask)

      # Create overlay for this mask
      overlay = Image.new('RGBA', im.size, (0, 0, 0, 0))
      overlay_draw = ImageDraw.Draw(overlay)

      # Create overlay for the mask
      color = (255, 255, 255, 200)
      for y in range(y0, y1):
          for x in range(x0, x1):
              if mask_array[y - y0, x - x0] > 128:  # Threshold for mask
                  overlay_draw.point((x, y), fill=color)

      # Save individual mask and its overlay
      mask_filename = f"{item['label']}_{i}_mask.png"
      overlay_filename = f"{item['label']}_{i}_overlay.png"

      mask.save(os.path.join(output_dir, mask_filename))

      # Create and save overlay
      composite = Image.alpha_composite(im.convert('RGBA'), overlay)
      composite.save(os.path.join(output_dir, overlay_filename))
      print(f"Saved mask and overlay for {item['label']} to {output_dir}")

def transcribe_audio_from_mic():
    client = get_gemini_client()
    if not client:
        return

    prompt = """
    Process the audio file and generate a detailed transcription.

    Requirements:
    1. Identify distinct speakers (e.g., Speaker 1, Speaker 2, or names if context allows).
    2. Provide accurate timestamps for each segment (Format: MM:SS).
    3. Detect the primary language of each segment.
    4. If the segment is in a language different than English, also provide the English translation.
    5. Identify the primary emotion of the speaker in this segment. You MUST choose exactly one of the following: Happy, Sad, Angry, Neutral.
    6. Provide a brief summary of the entire audio at the beginning.
    """

    # This is a placeholder for actual microphone input
    # In a real application, you would use a library like PyAudio to capture audio
    # and then pass it to the Gemini API.
    # For now, we'll use a mock audio file.
    audio_file = "path/to/your/mic/input.wav" # Replace with actual mic input logic

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[
          types.Content(
            parts=[
              types.Part(
                file_data=types.FileData(
                  file_uri=audio_file,
                  mime_type="audio/wav"
                )
              ),
              types.Part(
                text=prompt
              )
            ]
          )
        ],
        config=types.GenerateContentConfig(
          response_mime_type="application/json",
          response_schema=types.Schema(
            type=types.Type.OBJECT,
            properties={
              "summary": types.Schema(
                type=types.Type.STRING,
                description="A concise summary of the audio content.",
              ),
              "segments": types.Schema(
                type=types.Type.ARRAY,
                description="List of transcribed segments with speaker and timestamp.",
                items=types.Schema(
                  type=types.Type.OBJECT,
                  properties={
                    "speaker": types.Schema(type=types.Type.STRING),
                    "timestamp": types.Schema(type=types.Type.STRING),
                    "content": types.Schema(type=types.Type.STRING),
                    "language": types.Schema(type=types.Type.STRING),
                    "language_code": types.Schema(type=types.Type.STRING),
                    "translation": types.Schema(type=types.Type.STRING),
                    "emotion": types.Schema(
                      type=types.Type.STRING,
                      enum=["happy", "sad", "angry", "neutral"]
                    ),
                  },
                  required=["speaker", "timestamp", "content", "language", "language_code", "emotion"],
                ),
              ),
            },
            required=["summary", "segments"],
          ),
        ),
      )
    print(response.text)

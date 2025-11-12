from clients import GeminiClient

def test_gemini_basic():
    try:
        # Initialize client with the lightweight model
        client = GeminiClient(model=GeminiClient.Models.LITE)

        # Set a simple request prompt
        client.set_request("List three genres similar to fantasy books.")

        # Run the request
        client.send_request()

        # Get the result
        result = client.get_result()

        print("\n✅ Gemini client ran successfully!")
        print("Response:", result)

    except Exception as e:
        print("\n❌ Error during Gemini client test:")
        print(e)

if __name__ == "__main__":
    test_gemini_basic()

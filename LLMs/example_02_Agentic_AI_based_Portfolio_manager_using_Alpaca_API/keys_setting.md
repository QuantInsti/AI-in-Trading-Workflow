# How to set API KEYS

## For Google API KEY

Getting a **GOOGLE\_API\_KEY** generally involves using the **Google Cloud Console** to create a project, enable the specific Google service API you need, and then generate a key.

Here are the typical steps to follow:

### Steps to Get a Google API Key

1.  **Go to the Google Cloud Console (GCP):**
    * Navigate to the [Google Cloud Console](https://console.cloud.google.com/). You'll need to sign in with your Google account.

2.  **Create or Select a Project:**
    * If you don't have a project, you'll need to **create a new one**. A project is a container for all your Google Cloud resources, including API keys.
    * If you have an existing project, **select it** from the dropdown menu at the top of the page.

3.  **Enable the Necessary API:**
    * In the sidebar menu, go to **"APIs & Services"** and then **"Library."**
    * **Search for the specific Google API** you want to use (e.g., Maps JavaScript API, Places API, Gemini API, etc.).
    * Click on the API and then click the **"Enable"** button. This links the API to your project.

4.  **Create the API Key:**
    * In the sidebar menu, go to **"APIs & Services"** and select **"Credentials."**
    * Click on **"+ Create Credentials"** and choose **"API key."**
    * Your API key will be immediately generated and displayed in a dialog box. **Copy this key immediately**, as you may not be able to view the full key string again for security reasons.

5.  **Secure and Restrict Your Key (Highly Recommended!):**
    * For security, you should **restrict your API key** to prevent unauthorized use. While still on the "Credentials" page, click on the name of the key you just created.
    * Under "Application restrictions" and "API restrictions," configure rules to limit where the key can be used (e.g., specific websites, IP addresses) and which APIs it can access. **Always restrict your keys** to only what's necessary for your application. 

### Important Notes

* **Billing:** Many Google APIs, especially for Google Cloud or Google Maps Platform, require you to **enable billing** on your project before you can use the API key, even if the service offers a free tier.
* **Security:** **Never hardcode your API key** directly into public-facing code (like client-side JavaScript). It's best practice to use environment variables or a secure secret management service.
* **Specific APIs:** Some newer APIs, like the **Gemini API** for generative AI, also offer a simplified key creation process through the [Google AI Studio](https://aistudio.google.com/app/apikey) dashboard, which may automatically create a project for you.

-----

## For Tvaily API Key

Here is the step-by-step process, starting with how to get the key and then how to set it in different operating systems/environments.

1.  **Sign Up/Log In:** Go to the [Tavily AI website](https://tavily.com/). You will need to create an account or log in.
2.  **Access the Dashboard/API Keys:** Once logged in, navigate to your **dashboard** or the **API Keys** section.
3.  **Generate/Copy Key:** Generate a new API key if necessary, and **copy the key string** (it will typically start with `tvly-`).

-----

## For the Alpaca API Key

The environment variables **`APCA_API_KEY_ID`** and **`APCA_API_SECRET_KEY`** are used to authenticate with the **Alpaca API** (a commission-free stock and crypto trading platform).

You need to obtain your keys from the Alpaca dashboard:

1.  **Log in** to your Alpaca account (or sign up).
2.  Navigate to the **API Keys** section of your dashboard.
3.  Click the button to **view** or **generate** a new set of keys.
4.  You will receive two values: the **API Key ID** (for `APCA_API_KEY_ID`) and the **Secret Key** (for `APCA_API_SECRET_KEY`).
    > **Note:** The **Secret Key is only displayed once** upon generation for security reasons. Make sure to copy and save it securely immediately, otherwise you'll have to regenerate the keys.

-----

## For the Gmail App password

Setting your **Gmail credentials** in this format is typically done by setting the values within a **configuration file** (like a Python `.env` file, a shell script, or a specific application configuration file).

The crucial step for the `GMAIL_APP_PASSWORD` is that you **cannot use your regular Gmail password** if you have 2-Factor Authentication (2FA) enabled (which you should). You must generate a special **App Password**.

Here's the breakdown of how to handle each of these variables:

The `GMAIL_APP_PASSWORD` is a 16-character code that grants a non-browser application access to your Gmail account.

1.  **Enable 2-Step Verification (2FA):** You must have 2FA turned on for the Gmail account you are using as the sender (`SENDER_EMAIL`).
      * Go to your [Google Account Security Settings](https://myaccount.google.com/security).
      * Under "Signing in to Google," make sure "2-Step Verification" is **ON**.
2.  **Generate the App Password:**
      * While in the **Security** section, click on **"App Passwords."** (You will need to re-enter your Google password.)
      * In the "Select app" dropdown, choose **"Mail."**
      * In the "Select device" dropdown, choose **"Other (Custom name)"** and give it a name like "Email Reporter" or "Automation Script."
      * Click **"Generate."**
      * A **16-digit code** (with spaces, but you use it without spaces) will be displayed. **This is your `GMAIL_APP_PASSWORD`.**
      * **Copy this password immediately.** You will not see it again.

# Harvest AI

## How to Run

### Local Setup

1. Create a Python virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python wsgi.py
   ```

### Docker

You can also build and run using the provided Dockerfile.app:
```
docker build -f Dockerfile.app -t harvestai .
docker run -p 8000:8000 harvestai
```

### Hosting

Hosted at: AWS

---

### HarvestAI User Instructions

1. **Signup & Signin**

   * Create an account using your **email ID** and **WhatsApp number**.
   * Verify and login to start using the platform.

2. **Explore the Platform**

   * Navigate through the **Dashboard**, **Agri Marketplace**, **Alerts**, **Loans & Insurance**, and **Chatbot** sections.

3. **Hardware Overview**

   * View connected **Weed Detection Device**, **Tree Monitoring System**, and **Soil & Weather Sensors**.

4. **Add a Field**

   * Crop Name: *(search for a crop)*
   * Field Name: *South Field*
   * Purposes: *(add relevant purposes)*
   * Hub ID: *basestation\_1*
   * You can enter Hub ID manually or scan via QR.

5. **Go to Dashboard**

   * The newly added field will appear.
   * View **sensor readings** and **weather forecast data**.
   * Initially, no alerts will be shown.

6. **Trigger Alerts**

   * Click **Trigger Alert**.
   * System will take a short time to process and generate alerts.

7. **Upload Disease Image**

   * Upload the crop disease photo.
   * Wait while the system analyzes it.

8. **Check Alerts Again**

   * Refresh alerts.
   * A **disease-type alert** will be appended automatically.

9. **Visit Agri Marketplace**

   * Browse seeds, fertilizers, pesticides, equipment, and expert services.

10. **Use Chatbots**

    * **General Chatbot**: Ask farming-related questions.
    * **Field-Specific Chatbot**: Query insights about your added field.

11. **Manage Alerts**

    * Add **resolutions and comments** directly to alerts for tracking and follow-up.

12. **Loans & Insurance**

    * Explore tailored **loan & insurance options**.
    * Check **YouTube suggestions**, **gamification modules**, and **farm analysis insights**.
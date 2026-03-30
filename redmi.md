🧪 Playwright Test Report Analysis
📊 Test Summary
Total tests: 46
Passed: 6 ✅
Failed: 40 ❌
✔ Working Tests
Basic UI tests (title, link)
Working across all browsers
❌ Failing Tests
Login page rendering
Valid login redirect
Invalid login handling
Logout flow
📷 Test Report Screenshot

🚨 Error Details
❌ Error: ERR_CONNECTION_REFUSED

📌 Explanation
Test is trying to open:
http://127.0.0.1:8000/myesp/login/
But the server is not running
🖼 Screenshot Issue

📌 Explanation
Screenshot is blank because page did not load
📌 Reason
Backend server is not running
Playwright opened an empty page

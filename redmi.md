![alt text](image.png)
This page is a Playwright test report.

Total tests: 46
Passed: 6
Failed: 40

Basic tests (title, link) are working fine on all browsers.
Login/authentication tests are failing (login, logout, redirect).

Meaning:
Your app setup is okay, but the authentication feature or test setup has issues (backend, selectors, or timing).

![alt text](image-1.png)

Simple explanation:

Error: ERR_CONNECTION_REFUSED

Means:
Your test is trying to open
http://127.0.0.1:8000/myesp/login/
but server is not running

![alt text](image-2.png)

Simple explanation:

Screenshot is blank because
page never loaded

Reason:
Server is not running → so Playwright opened nothing → blank screen

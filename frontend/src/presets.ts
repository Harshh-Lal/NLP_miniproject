import type { CommitPreset } from './types';

export const PRESETS: CommitPreset[] = [
  {
    id: 'clean-feature',
    name: 'Compliant Feature',
    tag: 'PASS 1.00',
    badgeColor: 'text-[#3fb950] bg-[#238636]/15 border-[#238636]/40',
    description: 'Conventional prefix, active imperative verb, mentions key symbols, and touches safe modules.',
    message: 'feat: add token expiration check in validate_token and login',
    diff: `diff --git a/auth/session.py b/auth/session.py
index a1b2c3d..e4f5a6b 100644
--- a/auth/session.py
+++ b/auth/session.py
@@ -10,6 +10,10 @@ def validate_token(token):
     if not token:
         return False
+    if token.is_expired():
+        logger.warning("Token expired during validation")
+        raise TokenExpiredError("Token has expired")
     return True
diff --git a/controllers/user_controller.py b/controllers/user_controller.py
index 9876543..1234567 100644
--- a/controllers/user_controller.py
+++ b/controllers/user_controller.py
@@ -25,4 +25,8 @@ def login(request):
     user = authenticate(request.username, request.password)
     if not user:
         return Response("Unauthorized", status=401)
+    session.set_active(user.id)
+    return Response("OK")`,
  },
  {
    id: 'past-tense-fix',
    name: 'Non-Imperative Fix',
    tag: 'WARN 0.69',
    badgeColor: 'text-[#d29922] bg-[#bb8009]/15 border-[#bb8009]/40',
    description: 'Uses past-tense "fixed" instead of imperative "fix". Triggers NLP inflection rule and lemmatizer recommendation.',
    message: 'fixed login issue',
    diff: `diff --git a/auth/session.py b/auth/session.py
index a1b2c3d..e4f5a6b 100644
--- a/auth/session.py
+++ b/auth/session.py
@@ -10,6 +10,10 @@ def validate_token(token):
     if not token:
         return False
+    if token.is_expired():
+        logger.warning("Token expired during validation")
+        raise TokenExpiredError("Token has expired")
     return True
diff --git a/controllers/user_controller.py b/controllers/user_controller.py
index 9876543..1234567 100644
--- a/controllers/user_controller.py
+++ b/controllers/user_controller.py
@@ -25,4 +25,8 @@ def login(request):
     user = authenticate(request.username, request.password)
     if not user:
         return Response("Unauthorized", status=401)
+    session.set_active(user.id)
+    return Response("OK")`,
  },
  {
    id: 'silent-security-risk',
    name: 'Silent Security Risk',
    tag: 'FAIL (Risk Flag)',
    badgeColor: 'text-[#f85149] bg-[#da3633]/15 border-[#da3633]/40',
    description: 'Claims to be a simple chore, but sneaks modifications into auth security layer without mentioning auth/tokens.',
    message: 'chore: bump minor internal dependencies',
    diff: `diff --git a/auth/security_guard.py b/auth/security_guard.py
index 5544332..8877665 100644
--- a/auth/security_guard.py
+++ b/auth/security_guard.py
@@ -14,6 +14,8 @@ def verify_session_credentials(user_id, token):
-    if not strict_token_validation(token):
-        return False
+    # Bypass strict token check temporarily for tests
+    return True
diff --git a/requirements.txt b/requirements.txt
index 1122334..5566778 100644
--- a/requirements.txt
+++ b/requirements.txt
@@ -3,2 +3,2 @@ requests==2.31.0
-pyjwt==2.7.0
+pyjwt==2.8.0`,
  },
  {
    id: 'symbol-omission',
    name: 'Severe Symbol Omission',
    tag: 'WARN (Low Coverage)',
    badgeColor: 'text-[#d29922] bg-[#bb8009]/15 border-[#bb8009]/40',
    description: 'Modifies multiple major functions/classes, but commit message is overly generic and omits all symbol references.',
    message: 'refactor: general controller polish and updates',
    diff: `diff --git a/controllers/order_controller.py b/controllers/order_controller.py
index aa11bb2..cc33dd4 100644
--- a/controllers/order_controller.py
+++ b/controllers/order_controller.py
@@ -30,6 +30,12 @@ def calculate_cart_discount(cart):
+    if cart.has_promo_code():
+        return apply_seasonal_voucher(cart)
     return 0.0
+
+def finalize_invoice_checkout(order_id):
+    order = fetch_order(order_id)
+    return dispatch_fulfillment(order)`,
  },
  {
    id: 'clean-docs',
    name: 'Documentation Only',
    tag: 'NEUTRAL (Weight Rebalance)',
    badgeColor: 'text-[#58a6ff] bg-[#388bfd]/15 border-[#388bfd]/40',
    description: 'Pure Markdown documentation changes. Symbol coverage and risk are exempt (N/A); weights dynamically redistribute.',
    message: 'docs: update architecture guidelines and api schema specifications',
    diff: `diff --git a/docs/ARCHITECTURE.md b/docs/ARCHITECTURE.md
index 1111111..2222222 100644
--- a/docs/ARCHITECTURE.md
+++ b/docs/ARCHITECTURE.md
@@ -15,4 +15,10 @@
 ## Data Flow Pipeline
-All commits are verified through simple unit checks.
+All commits are parsed into unified diff ASTs and evaluated across four consistency dimensions:
+1. Imperative Mood Syntax
+2. Modified Symbol Coverage
+3. Architectural Safety Rules
+4. Stated vs Inferred Commit Type`,
  },
];

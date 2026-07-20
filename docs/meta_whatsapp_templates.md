# Meta WhatsApp Templates — submission content

How to use: Meta Business Suite → WhatsApp Manager → Message Templates → Create Template.
For each template below: paste the **Template Name** exactly (lowercase + underscores,
matches our DB slug), set **Category = Utility**, **Language = English**, paste the
**Body**, and enter the **Sample values** when Meta asks for examples during submission.

After a template is **approved**, go to the admin panel (`/admin/whatsapp-templates`,
or `PATCH /api/v1/admin/whatsapp-templates/{id}`) and set:
- `meta_template_name` → the exact name Meta approved it under
- `meta_template_language` → `en`
- `meta_template_status` → `approved`

That's it — no code deploy needed. The next time that event fires, it sends automatically.

---

## 1. wa_welcome_member
**Trigger:** New member enrolled. **Header:** none.

**Body:**
```
Welcome to EasyClaims, {{1}}! 🎉

You have been enrolled under *{{2}}*.

To upload your insurance policy document, visit:
{{3}}

For any queries, just send us a message.
```
**Sample values:** `{{1}}` Rahul Sharma · `{{2}}` Acme Corp · `{{3}}` https://easyclaims.in/upload

---

## 2. wa_new_partner
**Trigger:** Existing member added under a new partner. **Header:** none.

**Body:**
```
Hi {{1}}! 👋

You have been enrolled under a new partner on EasyClaims:
*{{2}}*

Your existing login credentials remain the same.
Log in to access your benefits: {{3}}

— EasyClaims Team
```
**Sample values:** `{{1}}` Rahul Sharma · `{{2}}` Acme Corp · `{{3}}` https://easyclaims.in/login

---

## 3. wa_membership_card
**Trigger:** Enrollment completion, sent with the membership card PDF. **Header:** Document (upload any sample PDF when submitting — the real member's card is sent at send-time via a link).

**Body:**
```
🎟 *EasyClaims Membership Card*

👤 *Member:* {{1}}
🏢 *Partner:* {{2}}
📋 *Plan:* {{3}}

*Benefits:*
• Family: {{4}} member(s)
• Policy Slots: {{5}}
• Claim Support: {{6}}
• Additional: {{7}}

Your membership card PDF is attached above.
Access your benefits: {{8}}

— EasyClaims Team
```
**Sample values:** `{{1}}` Rahul Sharma · `{{2}}` Acme Corp · `{{3}}` Gold Plan · `{{4}}` 4 · `{{5}}` 2 · `{{6}}` 24x7 · `{{7}}` AI Health Query Assistant, Tele-consultation (2 sessions) · `{{8}}` https://easyclaims.in/login

---

## 4. wa_policy_uploaded
**Trigger:** Member's policy document received. **Header:** none.

**Body:**
```
Hi {{1}}! ✅

Your {{2}} policy document has been received.

We are verifying your document. You will be notified once it is approved.
```
**Sample values:** `{{1}}` Rahul Sharma · `{{2}}` Health

---

## 5. wa_policy_rejected
**Trigger:** Uploaded document fails verification. **Header:** none.

**Body:**
```
Hi {{1}}! ❌

Your uploaded document for policy *{{2}}* could not be verified.

Reason: {{3}}

Please upload a valid insurance policy document.
```
**Sample values:** `{{1}}` Rahul Sharma · `{{2}}` HLT-2024-098765 · `{{3}}` Document is not a valid insurance policy.

---

## 6. wa_policy_approved
**Trigger:** Policy verified and goes active. **Header:** none.

**Body:**
```
Hi {{1}}! ✅

Your *{{2}}* policy (*{{3}}*) has been verified and is now *Active*.

You can view the full details anytime on your EasyClaims dashboard.
```
**Sample values:** `{{1}}` Rahul Sharma · `{{2}}` Health · `{{3}}` HLT-2024-098765

---

## 7. wa_policy_expired
**Trigger:** Policy end_date has passed. **Header:** none.

**Body:**
```
Hi {{1}}! 🔔

Your *{{2}}* policy (*{{3}}*) has expired.

Please upload your renewed policy document to maintain continuous coverage:
{{4}}

Need help? Just reply to this message.
```
**Sample values:** `{{1}}` Rahul Sharma · `{{2}}` Health · `{{3}}` HLT-2024-098765 · `{{4}}` https://easyclaims.in/upload

---

## 8. wa_upload_reminder
**Trigger:** Member enrolled but hasn't uploaded a policy document yet. **Header:** none.

**Body:**
```
Hi {{1}}! 👋

You are enrolled under *{{2}}* on EasyClaims, but we haven't received your insurance policy document yet.

Please upload it here: {{3}}

If you need help, just reply to this message.
```
**Sample values:** `{{1}}` Rahul Sharma · `{{2}}` Acme Corp · `{{3}}` https://easyclaims.in/upload

---

## 9. wa_policy_expiry_warning
**Trigger:** Policy expiring in N days. **Header:** none.

**Body:**
```
Hi {{1}}! ⚠️

Your *{{2}}* policy (*{{3}}*) is expiring in {{4}} day(s) on *{{5}}*.

Please renew your policy to avoid a lapse in coverage.
```
**Sample values:** `{{1}}` Rahul Sharma · `{{2}}` Health · `{{3}}` HLT-2024-098765 · `{{4}}` 7 · `{{5}}` 31-Mar-2026

---

## 10. wa_ticket_raised
**Trigger:** Member's claim ticket created via AI claim assist. **Header:** none.

**Body:**
```
Hi {{1}}! 🎫

Your claim request has been received.

*Ticket ID:* {{2}}
*Summary:* {{3}}

Our team will follow up with you shortly.
```
**Sample values:** `{{1}}` Rahul Sharma · `{{2}}` TCK-10234 · `{{3}}` Hospitalization claim for fever treatment

---

## 11. wa_claim_assigned_agent
**Trigger:** Claim assigned/reassigned to an agent. **Recipient:** the agent, not the member. **Header:** none.

**Body:**
```
Hi {{1}}! 📋

A claim has been assigned to you.

*Claim Number:* {{2}}
*Member:* {{3}}
*Policy:* {{4}}

— EasyClaims Team
```
**Sample values:** `{{1}}` Agent Priya · `{{2}}` CLM-5521 · `{{3}}` Rahul Sharma · `{{4}}` HLT-2024-098765

---

## 12. wa_claim_status_update_member
**Trigger:** Claim status changes. **Header:** none.

**Body:**
```
Hi {{1}}! 📋

Your claim *{{2}}* is now *{{3}}*.

{{4}}

— EasyClaims Team
```
**Sample values:** `{{1}}` Rahul Sharma · `{{2}}` CLM-5521 · `{{3}}` Approved · `{{4}}` Your reimbursement will be processed within 5-7 business days.

Note: `{{4}}` sends "No additional remarks." when there's no remark — Meta doesn't allow blank template parameters, so the code always fills something in.

---

## 13. wa_claim_submitted_admin
**Trigger:** New claim submitted. **Recipient:** superadmins, not the member. **Header:** none.

**Body:**
```
📋 New claim submitted

*Claim Number:* {{1}}
*Member:* {{2}}
*Assigned Agent:* {{3}}

— EasyClaims Team
```
**Sample values:** `{{1}}` CLM-5521 · `{{2}}` Rahul Sharma · `{{3}}` Agent Priya

---

## 14. wa_partner_welcome
**Trigger:** New partner (business) account created. **Recipient:** the partner's registered mobile, not a member. **Header:** none.

**Body:**
```
Welcome to EasyClaims, {{1}}! 🎉

Your partner account has been created and is ready to use.

Access your portal here: {{2}}

For any assistance, feel free to reply to this message.

— EasyClaims Team
```
**Sample values:** `{{1}}` Acme Corp · `{{2}}` https://easyclaims.in/login

Note: the original draft included an `{{3}}` Email variable, but Meta's automatic
classifier flags labeled `Login at:` / `Email:` pairs as Authentication-category
(OTP-style) content and rejects them under Utility. Dropped to 2 variables to avoid
that misclassification — `variable_order` in the DB was updated to match.

---

## Notes
- All 14 are transactional/**Utility** category — none are Marketing, so review is generally fast (often automated, minutes to a few hours).
- Only `wa_membership_card` needs a Document header (PDF).
- Hindi versions aren't included here (English only, matching current scope) — `MemberProfile.preferred_language` already supports `"hi"` for future use; add a second approved template per slug with `meta_template_language="hi"` later if needed, and extend `WhatsAppTemplateQuery` to pick language by member preference.
- Editing an **approved** template's wording later triggers Meta re-review. Prefer creating a new template (e.g. `wa_welcome_member_v2`), getting it approved, then updating `meta_template_name` in the admin panel — avoids any downtime on the old one while the new one is in review.

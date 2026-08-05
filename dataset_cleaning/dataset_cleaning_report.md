# ScopeGuard: Data Cleaning Report

## Dataset Cleaning

### Summary

**69 unrealistic scope combinations** were identified and removed from `scope_guard_dataset008.csv` to produce `scope_guard_dataset_cleaned.csv` (1,903 → 1,834 rows). The removed combinations pair Google services that serve fundamentally different purposes, making it implausible that any real application would request them together. These incoherent pairings would introduce noise into the training data.

> **Note:** This report is regenerated directly from `scope_guard_dataset008.csv`. That source file has 1,903 rows, not the 1,912 cited in the original report draft — so the post-removal total here (1,834) is 9 rows lower than the previously circulated `scope_guard_dataset_cleaned.csv` (1,843 rows). Those 9 extra rows (`SC-1903`–`SC-1911`) do not exist in `dataset008.csv` and were not part of this removal process; they'll need to be reconciled separately if the 1,843-row file is the intended target.

| Metric | Before | After |
| --- | --- | --- |
| Total rows | 1,903 | 1,834 |
| Rows removed | — | **69** |
| Low | 252 | 252 (0 removed) |
| Medium | 533 | 532 (1 removed) |
| High | 647 | 618 (29 removed) |
| Critical | 471 | 432 (39 removed) |

### Removals by Generation Strategy

The majority of removed combinations came from random generation strategies, which is expected since those strategies prioritize feature space coverage over realism:

| Strategy | Removed | % of 69 |
| --- | --- | --- |
| F: Randomly Generated Scope Combinations | 31 | 44.9% |
| B: Addition (student_gen) | 17 | 24.6% |
| H: Base Scope Combination + Random Addition | 7 | 10.1% |
| B: Addition (github manifest) | 3 | 4.3% |
| E: Plausable Cross Scope Combinations | 3 | 4.3% |
| C: Removal | 3 | 4.3% |
| G: Plausable Cross Scope Combinations + Random Addition | 2 | 2.9% |
| J: Bool Switching of Medium Risk Combinations | 1 | 1.4% |
| Student Created | 1 | 1.4% |
| A: Boolean Switching | 1 | 1.4% |

---

## Pattern 1: Fitness/Health + Unrelated Services (51 removed)

Google Fitness scopes access sensitive health data from wearable devices including blood glucose, blood pressure, heart rate, sleep patterns, body measurements, and physical activity. These are used exclusively by health and wellness applications. No legitimate health app would also need to manage chat spaces, administer Workspace domains, control cloud VMs, edit presentations, manage Firebase backends, automate Apps Script workflows, run BigQuery queries, manage YouTube channels, write blog posts, or access personal notes. Each pairing below represents two services with **no shared user population, no plausible workflow, and no documented precedent**.

| Pairing | Count | Why Unrealistic |
| --- | --- | --- |
| Fitness + Chat | 9 | Health tracking does not require sending or reading chat messages. |
| Fitness + Admin | 9 | Health monitoring apps do not manage organizational domains or user accounts. |
| Fitness + Firebase | 7 | App backend management has no connection to personal health monitoring. |
| Fitness + Apps Script | 5 | Health data from wearables is not part of the Workspace automation ecosystem. |
| Fitness + Compute | 5 | Wearable health apps have no connection to cloud VM management. |
| Fitness + BigQuery | 4 | Personal health data from wearables does not belong in a cloud data warehouse context. |
| Fitness + Keep | 4 | Personal notes management has no plausible connection to wearable health data. |
| Fitness + YouTube | 2 | Health data collection has no relationship to video channel management. |
| Fitness + Classroom | 2 | Educational course management has no connection to wearable health data. |
| Fitness + Cloud Storage | 2 | Cloud infrastructure storage has no connection to personal health monitoring. |
| Fitness + Full Gmail | 1 | Full email access has no relationship to fitness GPS or health data. |
| Fitness + Slides | 1 | Body measurements and health data have no connection to presentation editing. |

### Detailed List: Fitness Removals

| ID | Incoherent Pairing | Scopes Requested | Offline | Source Strategy |
| --- | --- | --- | --- | --- |
| SC-0337 | Fitness + Chat | openid profile email chat.messages contacts.readonly fitness.activity.read | No | B: Addition (student_gen) |
| SC-0364 | Fitness + Chat | openid profile email chat.messages drive.readonly fitness.activity.read | No | B: Addition (student_gen) |
| SC-0387 | Fitness + Chat | openid profile email firebase fitness.blood_glucose.read chat.messages | Yes | B: Addition (student_gen) |
| SC-0424 | Fitness + Chat | openid profile email calendar.events.owned chat.messages.readonly fitness.activity.read | No | B: Addition (student_gen) |
| SC-0457 | Fitness + Chat | openid profile email photoslibrary.appendonly chat.messages.readonly gmail.addons.current.message.readonly fitness.activity.read | No | B: Addition (student_gen) |
| SC-0885 | Fitness + Chat | chat.memberships fitness.blood_glucose.read presentations.readonly | Yes | F: Randomly Generated Scope Combinations |
| SC-0918 | Fitness + Chat | calendar.events gmail.readonly fitness.blood_glucose.read chat.delete | Yes | F: Randomly Generated Scope Combinations |
| SC-1201 | Fitness + Chat | openid profile email firebase fitness.blood_glucose.read chat.delete | Yes | H: Base Scope Combination + Random Addition |
| SC-1212 | Fitness + Chat | openid profile email gmail.addons.current.message.readonly chat.messages fitness.body.read | Yes | H: Base Scope Combination + Random Addition |
| SC-0362 | Fitness + Admin | openid profile email admin.reports.audit.readonly analytics.readonly spreadsheets drive.file fitness.activity.read | No | B: Addition (student_gen) |
| SC-0430 | Fitness + Admin | openid profile email gmail.send admin.datatransfer fitness.activity.read | No | B: Addition (student_gen) |
| SC-0888 | Fitness + Admin | userinfo.email fitness.blood_pressure.read admin.directory.rolemanagement script.projects.readonly compute | No | F: Randomly Generated Scope Combinations |
| SC-0931 | Fitness + Admin | fitness.blood_pressure.read admin.datatransfer fitness.sleep.read admin.reports.audit.readonly youtubepartner | Yes | F: Randomly Generated Scope Combinations |
| SC-0948 | Fitness + Admin | admin.directory.user groups gmail.addons.current.action.compose chat.spaces fitness.activity.read | No | F: Randomly Generated Scope Combinations |
| SC-0966 | Fitness + Admin | admin.directory.user photoslibrary.appendonly gmail.labels classroom.courses fitness.sleep.read | Yes | F: Randomly Generated Scope Combinations |
| SC-0990 | Fitness + Admin | calendar.calendars.readonly analytics.manage.users fitness.activity.write admin.reports.audit.readonly | No | F: Randomly Generated Scope Combinations |
| SC-0997 | Fitness + Admin | forms.body.readonly fitness.location.read calendar.calendarlist.readonly admin.reports.audit.readonly | Yes | F: Randomly Generated Scope Combinations |
| SC-1235 | Fitness + Admin | admin.directory.user admin.directory.group admin.directory.domain admin.datatransfer fitness.location.read | No | H: Base Scope Combination + Random Addition |
| SC-0026 | Fitness + Firebase | openid profile email firebase fitness.blood_glucose.read | Yes | Student Created |
| SC-0130 | Fitness + Firebase | openid profile email firebase fitness.blood_glucose.read | No | A: Boolean Switching |
| SC-0388 | Fitness + Firebase | openid profile email firebase fitness.blood_glucose.read gmail.send | Yes | B: Addition (student_gen) |
| SC-0389 | Fitness + Firebase | openid profile email firebase fitness.blood_glucose.read contacts.readonly | Yes | B: Addition (student_gen) |
| SC-0536 | Fitness + Firebase | openid profile firebase fitness.blood_glucose.read | Yes | C: Removal |
| SC-0537 | Fitness + Firebase | profile email firebase fitness.blood_glucose.read | Yes | C: Removal |
| SC-0539 | Fitness + Firebase | openid email firebase fitness.blood_glucose.read | Yes | C: Removal |
| SC-0251 | Fitness + Apps Script | script.projects drive spreadsheets gmail.send fitness.activity.read | Yes | B: Addition (github manifest) |
| SC-0414 | Fitness + Apps Script | openid profile email drive.scripts script.projects drive.activity fitness.activity.read | Yes | B: Addition (student_gen) |
| SC-0753 | Fitness + Apps Script | fitness.activity.write script.projects | No | E: Plausable Cross Scope Combinations |
| SC-0959 | Fitness + Apps Script | gmail.insert fitness.blood_pressure.read script.deployments | No | F: Randomly Generated Scope Combinations |
| SC-1066 | Fitness + Apps Script | fitness.heart_rate.read fitness.activity.write script.projects | Yes | J: Bool Switching of Medium Risk Combinations |
| SC-0303 | Fitness + Compute | cloud-platform compute fitness.activity.read | Yes | B: Addition (github manifest) |
| SC-0332 | Fitness + Compute | openid profile email firebase compute fitness.activity.read | No | B: Addition (student_gen) |
| SC-0911 | Fitness + Compute | calendar.settings.readonly compute fitness.activity.write gmail.addons.current.message.action | No | F: Randomly Generated Scope Combinations |
| SC-0934 | Fitness + Compute | fitness.location.read analytics.manage.users compute.readonly profile classroom.coursework.students | No | F: Randomly Generated Scope Combinations |
| SC-0941 | Fitness + Compute | fitness.heart_rate.read compute.readonly classroom.profile.emails devstorage.read_write | No | F: Randomly Generated Scope Combinations |
| SC-0305 | Fitness + BigQuery | devstorage.read_write bigquery fitness.activity.read | No | B: Addition (github manifest) |
| SC-0350 | Fitness + BigQuery | bigquery devstorage.read_write fitness.activity.read | Yes | B: Addition (student_gen) |
| SC-0428 | Fitness + BigQuery | bigquery devstorage.read_write spreadsheets fitness.activity.read | Yes | B: Addition (student_gen) |
| SC-0964 | Fitness + BigQuery | firebase analytics.manage.users bigquery.insertdata tasks.readonly fitness.location.read | Yes | F: Randomly Generated Scope Combinations |
| SC-0731 | Fitness + Keep | keep fitness.activity.write | No | E: Plausable Cross Scope Combinations |
| SC-0944 | Fitness + Keep | keep photoslibrary.readonly fitness.heart_rate.read | Yes | F: Randomly Generated Scope Combinations |
| SC-0972 | Fitness + Keep | analytics keep fitness.blood_glucose.read forms.body.readonly | Yes | F: Randomly Generated Scope Combinations |
| SC-1044 | Fitness + Keep | keep.readonly fitness.activity.read fitness.activity.write | Yes | G: Plausable Cross Scope Combinations + Random Addition |
| SC-0314 | Fitness + YouTube | openid profile email youtube drive.file fitness.activity.read | No | B: Addition (student_gen) |
| SC-0933 | Fitness + YouTube | mail.google.com (full Gmail) fitness.activity.write youtube.upload openid | No | F: Randomly Generated Scope Combinations |
| SC-0447 | Fitness + Classroom | openid profile email gmail.send classroom.profile.emails calendar.events.readonly fitness.activity.read | No | B: Addition (student_gen) |
| SC-0883 | Fitness + Classroom | calendar.app.created fitness.activity.read classroom.profile.emails user.phonenumbers.read calendar.readonly | No | F: Randomly Generated Scope Combinations |
| SC-0906 | Fitness + Cloud Storage | forms.body gmail.readonly drive.readonly devstorage.full_control fitness.body.read | No | F: Randomly Generated Scope Combinations |
| SC-0983 | Fitness + Cloud Storage | devstorage.read_write fitness.blood_glucose.read drive.appdata calendar.acls openid | Yes | F: Randomly Generated Scope Combinations |
| SC-0884 | Fitness + Full Gmail | mail.google.com (full Gmail) fitness.location.read firebase.messaging | Yes | F: Randomly Generated Scope Combinations |
| SC-0907 | Fitness + Slides | fitness.body.read presentations.readonly tasks | No | F: Randomly Generated Scope Combinations |

---

## Pattern 2: Admin + Consumer Services (10 removed)

Admin SDK scopes are used by IT departments and enterprise security tools to manage user accounts, groups, roles, and organizational policies. These serve a completely different audience (enterprise IT) than consumer services like YouTube (content creators), Blogger (writers), Photos (personal media), AdSense (publishers), or Firebase (mobile app developers). No real IT provisioning tool would also manage YouTube uploads or personal photo libraries.

| Pairing | Count | Why Unrealistic |
| --- | --- | --- |
| Admin + Firebase | 3 | Workspace domain admin and mobile app backend management are unrelated. |
| Admin + Photos | 3 | IT user provisioning has no connection to personal photo library management. |
| Admin + Blogger | 2 | Domain administration and blog management have no overlapping purpose. |
| Admin + AdSense | 1 | Domain administration and ad revenue management serve different audiences. |
| Admin + YouTube | 1 | IT domain administration and video channel management serve completely different audiences. |

### Detailed List: Admin Removals

| ID | Incoherent Pairing | Scopes Requested | Offline | Source Strategy |
| --- | --- | --- | --- | --- |
| SC-0692 | Admin + Firebase | admin.directory.user firebase.messaging | Yes | E: Plausable Cross Scope Combinations |
| SC-0980 | Admin + Firebase | drive.file admin.directory.rolemanagement firebase.messaging | Yes | F: Randomly Generated Scope Combinations |
| SC-1005 | Admin + Firebase | admin.datatransfer firebase.readonly | No | G: Plausable Cross Scope Combinations + Random Addition |
| SC-0946 | Admin + Photos | profile drive.file cloud-platform.read-only admin.datatransfer photoslibrary | No | F: Randomly Generated Scope Combinations |
| SC-0950 | Admin + Photos | admin.directory.group photoslibrary.appendonly admin.reports.audit.readonly | Yes | F: Randomly Generated Scope Combinations |
| SC-1223 | Admin + Photos | openid profile email photoslibrary.appendonly chat.messages.readonly gmail.addons.current.message.readonly admin.directory.user | No | H: Base Scope Combination + Random Addition |
| SC-0982 | Admin + Blogger | cloud-platform.read-only documents.readonly admin.directory.user blogger.readonly compute.readonly | No | F: Randomly Generated Scope Combinations |
| SC-0985 | Admin + Blogger | mail.google.com (full Gmail) admin.datatransfer blogger.readonly | No | F: Randomly Generated Scope Combinations |
| SC-0893 | Admin + AdSense | adsense.readonly admin.datatransfer user.gender.read | Yes | F: Randomly Generated Scope Combinations |
| SC-0970 | Admin + YouTube | youtubepartner documents admin.reports.audit.readonly | Yes | F: Randomly Generated Scope Combinations |

---

## Pattern 3: Keep + Enterprise Infrastructure (2 removed)

Google Keep scopes access personal notes and to-do lists. BigQuery is a cloud data warehouse for SQL analytics. Compute Engine manages virtual machines. No real application would simultaneously manage personal sticky notes and run data warehouse queries or provision cloud VMs.

### Detailed List: Keep Removals

| ID | Incoherent Pairing | Scopes Requested | Offline | Source Strategy |
| --- | --- | --- | --- | --- |
| SC-0943 | Keep + Compute | keep.readonly firebase.readonly presentations.readonly compute drive.photos.readonly | No | F: Randomly Generated Scope Combinations |
| SC-0949 | Keep + BigQuery | documents firebase.readonly keep bigquery.insertdata | No | F: Randomly Generated Scope Combinations |

---

## Pattern 4: Cloud Infrastructure + Personal Data (5 removed)

BigQuery and Compute Engine are developer infrastructure services. Personal consumer services like Contacts and Photos serve individual users. No real data pipeline tool needs access to someone's personal phone numbers, and no photo organizer needs to run BigQuery queries.

### Detailed List: Infrastructure Removals

| ID | Incoherent Pairing | Scopes Requested | Offline | Source Strategy |
| --- | --- | --- | --- | --- |
| SC-0427 | BigQuery + Contacts | bigquery devstorage.read_write spreadsheets contacts.readonly | Yes | B: Addition (student_gen) |
| SC-0929 | BigQuery + Contacts | bigquery.insertdata mail.google.com (full Gmail) user.phonenumbers.read | No | F: Randomly Generated Scope Combinations |
| SC-1204 | BigQuery + Contacts | bigquery.insertdata drive.readonly contacts.other.readonly | Yes | H: Base Scope Combination + Random Addition |
| SC-1183 | Compute + Contacts | openid profile email firebase compute user.phonenumbers.read | No | H: Base Scope Combination + Random Addition |
| SC-1189 | BigQuery + Photos | bigquery devstorage.read_write photoslibrary.appendonly | Yes | H: Base Scope Combination + Random Addition |

---

## Pattern 5: Blogger + Personal Data (1 removed)

Blogger is a content publishing platform. Blog management tools do not need access to personal contact information like phone numbers or email addresses.

### Detailed List: Blogger Removals

| ID | Incoherent Pairing | Scopes Requested | Offline | Source Strategy |
| --- | --- | --- | --- | --- |
| SC-0371 | Blogger + Contacts | openid profile email blogger analytics script.projects contacts.readonly | Yes | B: Addition (student_gen) |

# Removing Unrealistic Scope Combinations from `scope_guard_dataset008.csv`

**Basis for removal:** implausible *service* combinations, **excluding** health/fitness combinations (category T1), which are retained.
**Rows examined:** 1894 (every row in the dataset). 
**Rows flagged as implausible:** 190. **Rows retained under the T1 health exemption:** 53.
**Decision:** KEEP 1757 | REMOVE 137 (7.2% of the dataset).

> **Revision note.** An earlier version of this report removed all 190 flagged rows. Category **T1 — health / fitness data combined with an unrelated service — is no longer removed.** A request that pairs Fitness scopes with a mailbox, directory, chat product, cloud console or media service is precisely the shape of a malicious health-data acquisition attempt: an application with no wellness function reaching for health data alongside an exfiltration channel. Those combinations are realistic *as attacks*, which is what the risk model is meant to catch, so they are kept as positive examples. All 53 T1 rows are itemised in §5 for reference; they remain in the filtered dataset.

REMOVE decisions are itemised in §4; the retained T1 rows are itemised in §5. The complete keep/remove decision for all rows is machine-readable in `scope_guard_dataset008_keep_remove_decisions.csv`, and `scope_guard_dataset008_filtered.csv` holds the surviving rows.

---

## 1. Why this filter is needed

The dataset is built from three attested seed sets and then expanded by ten generation strategies. Four of those strategies (B, C, F, H) draw scopes uniformly at random, either from the full catalog or from a pool of commonly requested scopes, and attach them to an existing combination without any check on whether the resulting service mix corresponds to a real application. The generator already encodes a notion of which service pairs make sense — the `plausable_cross_patterns` list that drives Strategies E and G — but that constraint is never applied to the other strategies or back onto the seed sets.

The consequence is a class of rows whose risk label is driven by breadth and sensitivity that no consent screen would ever display. A model trained on them learns that Analytics plus Contacts plus Compute is a Critical request, when the useful discrimination is between requests a user might actually be asked to approve — or, for the attack classes the model does need to see, between those and requests that only *look* broad. These rows inflate the Critical and High classes specifically, since implausible mixes are almost always broad and cross-service.

## 2. Method

### 2.1 Service resolution

Each scope URL was mapped back to its catalog service. The mapping was validated by reproducing two columns the dataset already carries: predicted service counts matched `cross_service_breadth` and predicted maximum sensitivity matched `data_sensitivity` for all 1903 rows (0 mismatches). Note that the People API scopes (`user.*.read`, `directory.readonly`) resolve to **Contacts**, not Identity or Admin.

### 2.2 Plausibility of a service pair

A combination is assessed as the set of unordered service pairs it induces. A pair is treated as **plausible** if any of the following hold:

1. **Curated list.** The pair appears in the generator's own `plausable_cross_patterns` list (162 pairs). Reusing the project's existing judgement keeps the filter consistent with the data it is filtering.
2. **Identity is universal.** `openid`, `email`, `profile` and the profile scopes accompany every OAuth application, so Identity pairs with anything.
3. **Single service.** Both scopes belong to one service.
4. **Family closure.** Docs/Sheets/Slides, the five GCP services (Cloud, Compute, BigQuery, Cloud Storage, Firebase), and Analytics/AdSense are sibling products. If the curated list accepts any member of one family with any member of another, the whole family pair is accepted. This repairs asymmetries in the curated list — it admits Sheets + Cloud Storage but not Docs + Cloud Storage, and Admin + BigQuery but not Admin + Cloud Storage — that are omissions rather than judgements.
5. **Named archetype gap.** The pair appears in the list in Appendix A: pairs the curated list omits but that map onto a documented application archetype (Calendar + Drive for meeting-notes tooling, Gmail + Tasks for email-to-task capture, and so on). Each entry names the archetype that justifies it.

A combination is **flagged if any one of its pairs is implausible**, and kept otherwise. Flagged rows are removed unless an exemption in §2.3 or §2.4 applies. The rule is deliberately pair-local: one indefensible pairing is enough to make the whole request unrepresentable, and requiring several would keep three-service rows whose single bad pair is the only thing driving their breadth score.

### 2.3 Exemption for attested combinations

Rows sourced from **Published Attack Patterns** and **Github Manifest Combinations** are exempt. These are empirically observed — real client manifests and documented incident write-ups — so plausibility-by-archetype does not apply to them; a deliberately over-broad request is the phenomenon being modelled, not noise. The exemption extends to rows carrying an identical scope set to an attested seed, which covers the boolean-switched copies made by Strategy A. Derived rows that *add* or *remove* scopes are not exempt, because the derivation is synthetic.

Student Created rows are **not** exempt: they are hand-written hypotheticals, and three of them fail the filter.

### 2.4 Exemption for health-data combinations (T1)

Combinations that pair a Google Fitness scope with a service outside the wellness archetype are **flagged but not removed**. The plausibility argument against them is an argument about *legitimate* applications: no wellness app can justify a mailbox, a directory, a chat product, a cloud console or a media service under Google's health-data policy. That is exactly why the combination is worth keeping. An OAuth request of this shape is the signature of a malicious health-data acquisition attack — health scopes requested by a client with no health function, alongside a channel capable of moving the data off-platform — and a model trained to score consent screens should see it labelled at the top of the scale rather than never see it at all.

The exemption is defined by category assignment, not by the presence of a Fitness scope. A row is retained only if T1 is the category it was filed under. Rows that contain health data but were filed under **T0** (three or more broken pairings) are still removed: their breadth is not the attack pattern, it is uniform random sampling, and the health scope in them is incidental. Nine of the sixteen T0 rows are of this kind.

### 2.5 Removal categories

Every flagged row is assigned to exactly one category, by the highest-priority violation it contains. Priority runs T0 → T6, so a row combining health data with cloud infrastructure is filed under health (T1) rather than infrastructure (T3), and a row breaking three or more pairings is filed as sprawl (T0) regardless of content.

| Code | Category | Rows | Decision |
|---|---|---:|---|
| T0 | Multi-domain sprawl with no coherent application archetype | 16 | Remove |
| T1 | Health / fitness data combined with an unrelated service | 53 | **Retain** (§2.4) |
| T2 | Domain administration combined with a consumer or marketing service | 17 | Remove |
| T3 | Cloud / developer infrastructure combined with personal communication or PIM data | 43 | Remove |
| T4 | Marketing and monetization combined with personal data services | 32 | Remove |
| T5 | Consumer media combined with an unrelated productivity or enterprise service | 28 | Remove |
| T6 | Incoherent productivity / PIM pairing | 1 | Remove |
| | **Total flagged** | **190** | |
| | **Total removed** | **137** | |

Because the priority rule files a row under its single highest violation, seven T1 rows also break a pairing that would independently place them in T2–T5 (listed in §5.1). They are retained: the health scope dominates the interpretation of the request, and removing them would delete the attack pattern the exemption exists to preserve.

## 3. Summary of removals

### 3.1 By generation method

| Generation method | Rows in dataset | Retained (T1) | Removed | % removed |
|---|---:|---:|---:|---:|
| Strategy I: Low Sensitivity Service Scope Combinations Generation | 489 | 0 | 0 | 0.0% |
| Strategy C: Removal | 202 | 3 | 10 | 5.0% |
| Strategy J: Bool Switching of Medium Risk Combinations | 192 | 0 | 4 | 2.1% |
| Strategy G: Plausable Cross Scope Combinations With Random Scope Addition | 160 | 0 | 0 | 0.0% |
| Strategy E: Plausable Cross Scope Combinations | 154 | 0 | 0 | 0.0% |
| Strategy B: Addition (student_gen) | 147 | 18 | 28 | 19.0% |
| Strategy F: Randomly Generated Scope Combinations | 135 | 20 | 64 | 47.4% |
| Strategy A: Boolean Switching | 104 | 1 | 2 | 1.9% |
| Strategy H: Base Scope Combinations With Random Scope Addition | 100 | 4 | 18 | 18.0% |
| Strategy B: Addition (github manifest) | 97 | 6 | 9 | 9.3% |
| Student Created | 50 | 1 | 2 | 4.0% |
| Github Manifest Combinations | 33 | 0 | 0 | 0.0% |
| Published Attack Patterns | 21 | 0 | 0 | 0.0% |
| Strategy D: Within Service Combinations | 19 | 0 | 0 | 0.0% |
| **All** | **1903** | **53** | **137** | **7.2%** |

The concentration is exactly where the generator applies no plausibility constraint. Strategy F (uniform random sampling over the whole catalog) loses the largest share, followed by the random-addition strategies B and H. The T1 exemption softens every one of these figures — Strategy F falls from 62.2% to 47.4% and Strategy B (student_gen) from 31.3% to 19.0% — because random sampling reaches Fitness scopes as readily as any other, and those draws are now kept. Strategies D, E, G and I lose nothing: D and I stay within a single service, and E and G are built from the curated pair list by construction.

### 3.2 Effect on the label distribution

| Risk label | Before | Retained (T1) | Removed | After |
|---|---:|---:|---:|---:|
| Low | 252 | 0 | 0 | 252 |
| Medium | 533 | 1 | 4 | 529 |
| High | 647 | 23 | 64 | 583 |
| Critical | 471 | 29 | 69 | 402 |
| **Total** | **1903** | **53** | **137** | **1766** |

Removals fall almost entirely on Critical and High, and no Low-risk row is removed. This is the expected signature of the problem: implausible service mixes are broad and cross-service, so the point mapping scores them at the top of the scale. Pruning them both improves realism and reduces the over-representation of the Critical class.

Retaining T1 deliberately holds 29 Critical and 23 High rows in the dataset that the plausibility filter would otherwise have taken. This is a smaller correction to the class balance than the original filter produced, and that is the intended trade-off: the Critical class stays larger, but what remains in it includes the health-acquisition attack pattern rather than only benign-but-broad requests.

### 3.3 Category by generation method

| Category | Strategy A: Boolean Switching | Strategy B: Addition (github manifest) | Strategy B: Addition (student_gen) | Strategy C: Removal | Strategy F: Randomly Generated Scope Combinations | Strategy H: Base Scope Combinations With Random Scope Addition | Strategy J: Bool Switching of Medium Risk Combinations | Student Created |
|---|---|---|---|---|---|---|---|---|
| T0 | 0 | 0 | 1 | 0 | 14 | 1 | 0 | 0 |
| T2 | 1 | 0 | 2 | 3 | 9 | 1 | 0 | 1 |
| T3 | 0 | 3 | 14 | 0 | 18 | 5 | 3 | 0 |
| T4 | 1 | 6 | 7 | 3 | 11 | 3 | 0 | 1 |
| T5 | 0 | 0 | 4 | 4 | 11 | 8 | 1 | 0 |
| T6 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| **All** | **2** | **9** | **28** | **10** | **64** | **18** | **4** | **2** |

T1 is omitted: those rows are retained. Their distribution by generation method is in §5.

---

## 4. Removals

T1 is not listed here — see §5.

Scope URLs are abbreviated: the `https://www.googleapis.com/auth/` prefix is dropped.

### T0 — Multi-domain sprawl with no coherent application archetype

**16 rows removed.**

These combinations span four or more services and break three or more service pairings at once. No single application archetype explains them: they are the product of uniform random sampling over the scope catalog rather than of any development pattern. They are the clearest false-positive risk in the dataset, because the label pipeline scores them Critical on breadth alone while nothing resembling them would ever reach a consent screen.

#### Strategy B: Addition (student_gen) (1 row)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0362 | Admin, Analytics, Drive, Fitness, Identity, Sheets | Admin + Analytics; Admin + Fitness; Analytics + Fitness | Critical | openid, profile, email, admin.reports.audit.readonly, analytics.readonly, spreadsheets, drive.file, fitness.activity.read |

#### Strategy F: Randomly Generated Scope Combinations (14 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0887 | AdSense, Calendar, Cloud Storage, Contacts, Tasks | AdSense + Calendar; AdSense + Contacts; AdSense + Tasks; Calendar + Cloud Storage; Cloud Storage + Tasks | Critical | calendar.events, adsense.readonly, contacts.readonly, tasks, devstorage.read_only |
| SC-0911 | Calendar, Compute, Fitness, Gmail | Calendar + Compute; Compute + Fitness; Fitness + Gmail | Critical | calendar.settings.readonly, compute, fitness.activity.write, gmail.addons.current.message.action |
| SC-0934 | Analytics, Classroom, Compute, Fitness, Identity | Analytics + Classroom; Analytics + Fitness; Classroom + Fitness; Compute + Fitness | High | fitness.location.read, analytics.manage.users, compute.readonly, profile, classroom.coursework.students |
| SC-0941 | Classroom, Cloud Storage, Compute, Fitness | Classroom + Fitness; Cloud Storage + Fitness; Compute + Fitness | High | fitness.heart_rate.read, compute.readonly, classroom.profile.emails, devstorage.read_write |
| SC-0948 | Admin, Chat, Fitness, Gmail, Groups | Admin + Fitness; Chat + Fitness; Fitness + Gmail; Fitness + Groups | Critical | admin.directory.user, groups, gmail.addons.current.action.compose, chat.spaces, fitness.activity.read |
| SC-0963 | Analytics, BigQuery, Calendar, Contacts | Analytics + Calendar; Analytics + Contacts; BigQuery + Calendar | High | analytics.readonly, calendar.readonly, bigquery.insertdata, user.addresses.read |
| SC-0964 | Analytics, BigQuery, Firebase, Fitness, Tasks | Analytics + Fitness; Analytics + Tasks; BigQuery + Fitness; BigQuery + Tasks; Firebase + Fitness; Firebase + Tasks | Critical | firebase, analytics.manage.users, bigquery.insertdata, tasks.readonly, fitness.location.read |
| SC-0966 | Admin, Classroom, Fitness, Gmail, Photos | Admin + Fitness; Admin + Photos; Classroom + Fitness; Classroom + Photos; Fitness + Gmail | Critical | admin.directory.user, photoslibrary.appendonly, gmail.labels, classroom.courses, fitness.sleep.read |
| SC-0972 | Analytics, Fitness, Forms, Keep | Analytics + Fitness; Analytics + Forms; Analytics + Keep; Forms + Keep | Critical | analytics, keep, fitness.blood_glucose.read, forms.body.readonly |
| SC-0982 | Admin, Blogger, Cloud, Compute, Docs | Admin + Blogger; Blogger + Cloud; Blogger + Compute | Critical | cloud-platform.read-only, documents.readonly, admin.directory.user, blogger.readonly, compute.readonly |
| SC-0990 | Admin, Analytics, Calendar, Fitness | Admin + Analytics; Admin + Fitness; Analytics + Calendar; Analytics + Fitness | Critical | calendar.calendars.readonly, analytics.manage.users, fitness.activity.write, admin.reports.audit.readonly |
| SC-0994 | AdSense, BigQuery, Chat, Drive, Firebase | AdSense + Chat; BigQuery + Chat; Chat + Firebase | High | bigquery.insertdata, firebase.messaging, drive.activity.readonly, adsense, chat.messages.readonly |
| SC-0996 | Admin, Analytics, Classroom, Gmail, YouTube | Admin + Analytics; Admin + YouTube; Analytics + Classroom | Critical | classroom.courses, youtube.upload, admin.directory.rolemanagement, gmail.modify, analytics |
| SC-0998 | Analytics, Chat, Cloud, Contacts, Gmail | Analytics + Chat; Analytics + Contacts; Chat + Cloud | Critical | analytics.edit, cloud-platform, gmail.settings.sharing, user.gender.read, chat.memberships |

#### Strategy H: Base Scope Combinations With Random Scope Addition (1 row)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-1244 | Calendar, Cloud Storage, Contacts, Drive, Gmail, Photos, YouTube | Calendar + Cloud Storage; Calendar + Photos; Contacts + YouTube | Critical | gmail.modify, drive, calendar, contacts, youtube, photoslibrary, devstorage.read_only |

### T2 — Domain administration combined with a consumer or marketing service

**17 rows removed.**

Workspace administration scopes are granted to domain-management tooling, which operates over the Workspace suite itself. The curated list accordingly admits Admin alongside Gmail, Drive, Contacts, Sheets, Apps Script, Classroom and the GCP services, and this analysis further admits Calendar, Chat, Forms, Tasks, Docs, Slides and Groups as suite-internal administration. What remains below pairs domain administration with consumer or marketing products that a Workspace administrator does not administer at all — Google Photos, YouTube, Blogger, AdSense, Analytics and Fitness are outside the Workspace tenancy boundary.

#### Strategy A: Boolean Switching (1 row)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0121 | Admin, Analytics, Drive, Identity, Sheets | Admin + Analytics | Critical | openid, profile, email, admin.reports.audit.readonly, analytics.readonly, spreadsheets, drive.file |

#### Strategy B: Addition (student_gen) (2 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0361 | Admin, Analytics, Drive, Gmail, Identity, Sheets | Admin + Analytics | Critical | openid, profile, email, admin.reports.audit.readonly, analytics.readonly, spreadsheets, drive.file, gmail.send |
| SC-0363 | Admin, Analytics, Calendar, Drive, Identity, Sheets | Admin + Analytics; Analytics + Calendar | Critical | openid, profile, email, admin.reports.audit.readonly, analytics.readonly, spreadsheets, drive.file, calendar.events.readonly |

#### Strategy C: Removal (3 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0515 | Admin, Analytics, Drive, Identity, Sheets | Admin + Analytics | Critical | openid, profile, admin.reports.audit.readonly, analytics.readonly, spreadsheets, drive.file |
| SC-0516 | Admin, Analytics, Drive, Identity, Sheets | Admin + Analytics | Critical | profile, email, admin.reports.audit.readonly, analytics.readonly, spreadsheets, drive.file |
| SC-0517 | Admin, Analytics, Drive, Identity, Sheets | Admin + Analytics | Critical | openid, email, admin.reports.audit.readonly, analytics.readonly, spreadsheets, drive.file |

#### Strategy F: Randomly Generated Scope Combinations (9 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0871 | Admin, Analytics, YouTube | Admin + Analytics; Admin + YouTube | Critical | admin.directory.user, youtube, analytics |
| SC-0876 | Admin, Analytics, Classroom | Admin + Analytics; Analytics + Classroom | Critical | classroom.courses.readonly, admin.directory.user.security, analytics.readonly |
| SC-0880 | Admin, Analytics, Drive, Forms | Admin + Analytics; Analytics + Forms | Critical | drive.file, admin.directory.user.readonly, admin.directory.user, analytics.manage.users, forms.body.readonly |
| SC-0893 | AdSense, Admin, Contacts | AdSense + Admin; AdSense + Contacts | Critical | adsense.readonly, admin.datatransfer, user.gender.read |
| SC-0901 | Admin, Analytics, Tasks | Admin + Analytics; Analytics + Tasks | Critical | admin.directory.group, tasks, analytics |
| SC-0946 | Admin, Cloud, Drive, Identity, Photos | Admin + Photos | Critical | profile, drive.file, cloud-platform.read-only, admin.datatransfer, photoslibrary |
| SC-0950 | Admin, Photos | Admin + Photos | Critical | admin.directory.group, photoslibrary.appendonly, admin.reports.audit.readonly |
| SC-0970 | Admin, Docs, YouTube | Admin + YouTube | Critical | youtubepartner, documents, admin.reports.audit.readonly |
| SC-0985 | Admin, Blogger, Gmail | Admin + Blogger | Critical | mail.google.com/, admin.datatransfer, blogger.readonly |

#### Strategy H: Base Scope Combinations With Random Scope Addition (1 row)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-1223 | Admin, Chat, Gmail, Identity, Photos | Admin + Photos | Critical | openid, profile, email, photoslibrary.appendonly, chat.messages.readonly, gmail.addons.current.message.readonly, admin.directory.user |

#### Student Created (1 row)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0017 | Admin, Analytics, Drive, Identity, Sheets | Admin + Analytics | Critical | openid, profile, email, admin.reports.audit.readonly, analytics.readonly, spreadsheets, drive.file |

### T3 — Cloud / developer infrastructure combined with personal communication or PIM data

**43 rows removed.**

Cloud Platform, Compute, BigQuery, Cloud Storage and Firebase scopes are requested by developer and data tooling. Their legitimate consumer-side counterparts are document and file services (Drive, Docs, Sheets), which appear in export, backup and pipeline archetypes, plus Gmail and Contacts for the notification and CRM-sync patterns already in the curated list. The combinations below instead pair infrastructure management with personal calendars, notes, task lists, chat messages or health data. There is no deployment, analytics or backup workflow in which a service account manager also needs the operator's personal to-do list.

#### Strategy B: Addition (github manifest) (3 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0260 | Analytics, BigQuery, Chat | Analytics + Chat; BigQuery + Chat | High | analytics, bigquery, chat.messages |
| SC-0302 | Cloud, Compute, Tasks | Cloud + Tasks; Compute + Tasks | Critical | cloud-platform, compute, tasks |
| SC-0304 | BigQuery, Chat, Cloud Storage | BigQuery + Chat; Chat + Cloud Storage | High | devstorage.read_write, bigquery, chat.messages |

#### Strategy B: Addition (student_gen) (14 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0321 | Cloud Storage, Drive, Identity, Tasks | Cloud Storage + Tasks | Critical | openid, profile, email, devstorage.read_write, drive.file, tasks |
| SC-0331 | Compute, Firebase, Identity, Tasks | Compute + Tasks; Firebase + Tasks | High | openid, profile, email, firebase, compute, tasks |
| SC-0333 | Calendar, Compute, Firebase, Identity | Calendar + Compute; Calendar + Firebase | High | openid, profile, email, firebase, compute, calendar.events.readonly |
| SC-0351 | BigQuery, Chat, Cloud Storage | BigQuery + Chat; Chat + Cloud Storage | High | bigquery, devstorage.read_write, chat.messages |
| SC-0352 | Apps Script, Calendar, Firebase, Identity, Sheets | Calendar + Firebase | Critical | openid, profile, email, firebase, spreadsheets, script.deployments, script.projects, calendar.events.readonly |
| SC-0353 | Apps Script, Firebase, Identity, Sheets, Tasks | Firebase + Tasks | Critical | openid, profile, email, firebase, spreadsheets, script.deployments, script.projects, tasks |
| SC-0354 | Apps Script, Chat, Firebase, Identity, Sheets | Chat + Firebase | Critical | openid, profile, email, firebase, spreadsheets, script.deployments, script.projects, chat.messages |
| SC-0396 | BigQuery, Chat, Drive | BigQuery + Chat | High | bigquery.insertdata, drive.readonly, chat.messages |
| SC-0398 | BigQuery, Drive, Tasks | BigQuery + Tasks | High | bigquery.insertdata, drive.readonly, tasks |
| SC-0426 | BigQuery, Chat, Cloud Storage, Sheets | BigQuery + Chat; Chat + Cloud Storage | Critical | bigquery, devstorage.read_write, spreadsheets, chat.messages |
| SC-0438 | Calendar, Compute, Firebase, Identity, Sheets | Calendar + Compute; Calendar + Firebase | High | openid, profile, email, compute.readonly, firebase.readonly, spreadsheets, calendar.events.readonly |
| SC-0439 | Compute, Firebase, Identity, Sheets, Tasks | Compute + Tasks; Firebase + Tasks | High | openid, profile, email, compute.readonly, firebase.readonly, spreadsheets, tasks |
| SC-0440 | Chat, Compute, Firebase, Identity, Sheets | Chat + Compute; Chat + Firebase | High | openid, profile, email, compute.readonly, firebase.readonly, spreadsheets, chat.messages |
| SC-0442 | Analytics, Firebase, Identity, Tasks | Analytics + Tasks; Firebase + Tasks | High | openid, profile, email, firebase.readonly, analytics.readonly, tasks |

#### Strategy F: Randomly Generated Scope Combinations (18 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0863 | Calendar, Cloud Storage, Drive, Gmail | Calendar + Cloud Storage | Critical | calendar.acls.readonly, drive.activity, devstorage.read_only, gmail.metadata, gmail.labels |
| SC-0865 | Blogger, Cloud Storage, Docs, Gmail, YouTube | Blogger + Cloud Storage | Critical | devstorage.full_control, documents, blogger, youtube, gmail.addons.current.action.compose |
| SC-0866 | Calendar, Cloud Storage, Identity, Photos, YouTube | Calendar + Cloud Storage; Calendar + Photos | High | devstorage.read_only, photoslibrary.readonly.appcreateddata, youtube, calendar.readonly, email |
| SC-0877 | Calendar, Cloud Storage, Forms, Tasks | Calendar + Cloud Storage; Cloud Storage + Tasks | High | calendar.events.owned.readonly, forms.body, tasks, devstorage.read_write |
| SC-0892 | Calendar, Firebase, Identity, Slides, YouTube | Calendar + Firebase | High | presentations, youtube, firebase.readonly, profile, calendar.events.freebusy |
| SC-0894 | BigQuery, Chat, Cloud Storage | BigQuery + Chat; Chat + Cloud Storage | High | bigquery, chat.spaces, devstorage.read_only |
| SC-0898 | Calendar, Compute, Drive | Calendar + Compute | High | drive.photos.readonly, compute.readonly, calendar.acls |
| SC-0902 | Calendar, Contacts, Firebase, YouTube | Calendar + Firebase; Contacts + YouTube | Critical | firebase.readonly, calendar.readonly, user.gender.read, youtubepartner |
| SC-0920 | Calendar, Cloud, Contacts, Slides | Calendar + Cloud | Critical | calendar.readonly, presentations, contacts, user.addresses.read, cloud-platform |
| SC-0927 | BigQuery, Calendar, Chat | BigQuery + Calendar; BigQuery + Chat | High | calendar.app.created, bigquery.insertdata, chat.messages |
| SC-0939 | Calendar, Cloud Storage, Contacts, Docs, Gmail | Calendar + Cloud Storage | Critical | gmail.addons.current.action.compose, calendar.app.created, devstorage.read_only, documents, user.addresses.read |
| SC-0943 | Compute, Drive, Firebase, Keep, Slides | Compute + Keep; Firebase + Keep | High | keep.readonly, firebase.readonly, presentations.readonly, compute, drive.photos.readonly |
| SC-0949 | BigQuery, Docs, Firebase, Keep | BigQuery + Keep; Firebase + Keep | High | documents, firebase.readonly, keep, bigquery.insertdata |
| SC-0961 | Apps Script, Chat, Cloud Storage, Drive, Gmail | Chat + Cloud Storage | Critical | gmail.readonly, chat.messages, devstorage.read_write, script.projects, drive.metadata |
| SC-0969 | AdSense, Blogger, Firebase, Slides | Blogger + Firebase | High | presentations.readonly, adsense.readonly, firebase.messaging, blogger |
| SC-0971 | AdSense, Apps Script, Chat, Cloud Storage | AdSense + Chat; Chat + Cloud Storage | High | script.projects, adsense.readonly, chat.messages, devstorage.read_only |
| SC-0974 | Firebase, Identity, Keep | Firebase + Keep | High | email, firebase, keep.readonly |
| SC-0999 | Calendar, Compute, Gmail, Identity, Tasks | Calendar + Compute; Compute + Tasks | High | compute.readonly, gmail.settings.sharing, userinfo.profile, tasks.readonly, calendar.events.freebusy |

#### Strategy H: Base Scope Combinations With Random Scope Addition (5 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-1179 | Calendar, Cloud Storage, Drive, Identity | Calendar + Cloud Storage | High | openid, profile, email, devstorage.read_write, drive.file, calendar.acls.readonly |
| SC-1218 | Chat, Compute, Firebase, Identity, Sheets | Chat + Compute; Chat + Firebase | Critical | openid, profile, email, compute.readonly, firebase.readonly, spreadsheets, chat.memberships |
| SC-1219 | Analytics, Calendar, Firebase, Identity | Analytics + Calendar; Calendar + Firebase | Medium | openid, profile, email, firebase.readonly, analytics.readonly, calendar.events.owned.readonly |
| SC-1262 | Analytics, BigQuery, Chat | Analytics + Chat; BigQuery + Chat | High | analytics, bigquery, chat.spaces |
| SC-1269 | Calendar, Chat, Cloud Storage | Calendar + Cloud Storage; Chat + Cloud Storage | High | chat.messages, chat.spaces, calendar.events.readonly, devstorage.read_only |

#### Strategy J: Bool Switching of Medium Risk Combinations (3 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0261 | Analytics, BigQuery, Tasks | Analytics + Tasks; BigQuery + Tasks | High | analytics, bigquery, tasks |
| SC-0307 | Calendar, Cloud, Compute | Calendar + Cloud; Calendar + Compute | Medium | cloud-platform.read-only, compute.readonly, calendar.events.readonly |
| SC-0962 | Calendar, Cloud Storage, Firebase | Calendar + Cloud Storage; Calendar + Firebase | High | devstorage.full_control, firebase.messaging, calendar.app.created |

### T4 — Marketing and monetization combined with personal data services

**32 rows removed.**

Analytics and AdSense scopes serve reporting and monetization tooling, which reads metrics and writes them into documents and warehouses. The curated list captures those flows (Sheets, Docs, Drive, BigQuery, Cloud Storage, Blogger, YouTube). The combinations below attach revenue or traffic reporting to personal address books, calendars, task lists, notes, chat messages, classroom rosters or health data. Marketing reporting has no read path into any of those, and the pairing exists in the dataset only because the augmentation strategies drew a scope at random from the full catalog.

#### Strategy A: Boolean Switching (1 row)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0115 | Analytics, Contacts, Identity | Analytics + Contacts | Critical | openid, profile, email, userinfo.profile, analytics, user.addresses.read |

#### Strategy B: Addition (github manifest) (6 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0256 | Analytics, Sheets, Tasks | Analytics + Tasks | High | analytics.readonly, spreadsheets, tasks |
| SC-0257 | Analytics, Contacts, Sheets | Analytics + Contacts | High | analytics.readonly, spreadsheets, contacts.readonly |
| SC-0258 | Analytics, Calendar, Sheets | Analytics + Calendar | High | analytics.readonly, spreadsheets, calendar.events.readonly |
| SC-0259 | Analytics, BigQuery, Contacts | Analytics + Contacts | High | analytics, bigquery, contacts.readonly |
| SC-0268 | Analytics, Tasks, YouTube | Analytics + Tasks | High | youtube, analytics.readonly, tasks |
| SC-0270 | Analytics, Contacts, YouTube | Analytics + Contacts; Contacts + YouTube | Critical | youtube, analytics.readonly, contacts.readonly |

#### Strategy B: Addition (student_gen) (7 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0343 | Analytics, Calendar, Contacts, Identity | Analytics + Calendar; Analytics + Contacts | High | openid, profile, email, userinfo.profile, analytics, user.addresses.read, calendar.events.readonly |
| SC-0344 | Analytics, Contacts, Gmail, Identity | Analytics + Contacts | Critical | openid, profile, email, userinfo.profile, analytics, user.addresses.read, gmail.send |
| SC-0370 | Analytics, Apps Script, Blogger, Calendar, Identity | Analytics + Calendar; Blogger + Calendar | High | openid, profile, email, blogger, analytics, script.projects, calendar.events.readonly |
| SC-0371 | Analytics, Apps Script, Blogger, Contacts, Identity | Analytics + Contacts; Blogger + Contacts | Critical | openid, profile, email, blogger, analytics, script.projects, contacts.readonly |
| SC-0405 | Analytics, Chat, Identity, Sheets | Analytics + Chat | Critical | openid, profile, email, analytics.readonly, spreadsheets, chat.messages |
| SC-0406 | Analytics, Calendar, Identity, Sheets | Analytics + Calendar | Critical | openid, profile, email, analytics.readonly, spreadsheets, calendar.events.readonly |
| SC-0454 | AdSense, Analytics, Identity, Tasks | AdSense + Tasks; Analytics + Tasks | High | openid, profile, email, adsense.readonly, analytics.readonly, tasks |

#### Strategy C: Removal (3 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0499 | Analytics, Contacts, Identity | Analytics + Contacts | High | openid, profile, userinfo.profile, analytics, user.addresses.read |
| SC-0500 | Analytics, Contacts, Identity | Analytics + Contacts | High | openid, email, userinfo.profile, analytics, user.addresses.read |
| SC-0502 | Analytics, Contacts, Identity | Analytics + Contacts | High | profile, email, userinfo.profile, analytics, user.addresses.read |

#### Strategy F: Randomly Generated Scope Combinations (11 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0868 | Analytics, Calendar, Gmail, Tasks | Analytics + Calendar; Analytics + Tasks | Critical | tasks, gmail.send, analytics.readonly, calendar.calendars.readonly |
| SC-0873 | Analytics, Contacts, Drive, Forms | Analytics + Contacts; Analytics + Forms | Critical | drive.metadata.readonly, contacts.other.readonly, forms, contacts, analytics.edit |
| SC-0882 | Analytics, Gmail, Tasks | Analytics + Tasks | Critical | analytics, mail.google.com/, tasks |
| SC-0909 | Analytics, Calendar, Drive | Analytics + Calendar | High | analytics.readonly, calendar.acls, drive.metadata.readonly |
| SC-0923 | Analytics, Chat, Identity | Analytics + Chat | Medium | userinfo.email, analytics.readonly, chat.messages.readonly |
| SC-0940 | Analytics, Calendar, Forms | Analytics + Calendar; Analytics + Forms | High | forms.body, calendar.calendars.readonly, analytics |
| SC-0942 | AdSense, Blogger, Forms | AdSense + Forms; Blogger + Forms | High | adsense.readonly, blogger.readonly, forms.currentonly |
| SC-0952 | Analytics, Contacts, Gmail | Analytics + Contacts | High | analytics.edit, user.birthday.read, gmail.settings.basic |
| SC-0954 | AdSense, Cloud Storage, Drive, Forms | AdSense + Forms | Critical | devstorage.full_control, forms.body.readonly, drive.readonly, adsense |
| SC-0957 | AdSense, Calendar, Identity | AdSense + Calendar | Medium | adsense.readonly, calendar.calendarlist.readonly, email |
| SC-0993 | AdSense, Compute, Contacts, Gmail, YouTube | AdSense + Contacts; Contacts + YouTube | Critical | gmail.readonly, directory.readonly, adsense, compute.readonly, youtube |

#### Strategy H: Base Scope Combinations With Random Scope Addition (3 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-1187 | Analytics, Contacts, Identity, Photos | Analytics + Contacts; Analytics + Photos | High | openid, profile, email, userinfo.profile, analytics, user.addresses.read, photoslibrary.readonly.appcreateddata |
| SC-1195 | Analytics, Apps Script, Blogger, Chat, Identity | Analytics + Chat; Blogger + Chat | Critical | openid, profile, email, blogger, analytics, script.projects, chat.memberships |
| SC-1261 | Analytics, Calendar, Sheets | Analytics + Calendar | High | analytics.readonly, spreadsheets, calendar |

#### Student Created (1 row)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0011 | Analytics, Contacts, Identity | Analytics + Contacts | High | openid, profile, email, userinfo.profile, analytics, user.addresses.read |

### T5 — Consumer media combined with an unrelated productivity or enterprise service

**28 rows removed.**

Photos, YouTube and Blogger are consumer media services. Their realistic companions are file storage, documents, other media and monetization, all of which the curated list and the archetype-gap list already admit. The remaining pairings attach media libraries to address books, calendars, form responses, notes or classroom data, which correspond to no publishing, backup or creator workflow.

#### Strategy B: Addition (student_gen) (4 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0315 | Contacts, Drive, Identity, YouTube | Contacts + YouTube | Critical | openid, profile, email, youtube, drive.file, contacts.readonly |
| SC-0400 | Contacts, Drive, Identity, YouTube | Contacts + YouTube | Critical | openid, profile, email, drive.readonly, youtube.upload, contacts.readonly |
| SC-0411 | Blogger, Docs, Identity, Tasks | Blogger + Tasks | High | openid, profile, email, blogger, documents.readonly, tasks |
| SC-0412 | Blogger, Calendar, Docs, Identity | Blogger + Calendar | High | openid, profile, email, blogger, documents.readonly, calendar.events.readonly |

#### Strategy C: Removal (4 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0639 | Contacts, Drive, Gmail, Photos, YouTube | Contacts + YouTube | Critical | gmail.modify, drive, contacts, youtube, photoslibrary |
| SC-0640 | Calendar, Contacts, Drive, Photos, YouTube | Calendar + Photos; Contacts + YouTube | Critical | drive, calendar, contacts, youtube, photoslibrary |
| SC-0641 | Calendar, Contacts, Drive, Gmail, YouTube | Contacts + YouTube | Critical | gmail.modify, drive, calendar, contacts, youtube |
| SC-0642 | Calendar, Drive, Gmail, Photos, YouTube | Calendar + Photos | Critical | gmail.modify, drive, calendar, youtube, photoslibrary |

#### Strategy F: Randomly Generated Scope Combinations (11 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0869 | Chat, Contacts, YouTube | Contacts + YouTube | High | youtubepartner, chat.memberships, user.organization.read |
| SC-0881 | Calendar, Photos, Tasks, YouTube | Calendar + Photos | High | calendar.calendarlist.readonly, tasks.readonly, photoslibrary.readonly.appcreateddata, calendar.calendarlist, youtubepartner |
| SC-0897 | Cloud Storage, Contacts, YouTube | Contacts + YouTube | High | devstorage.read_only, user.birthday.read, youtube |
| SC-0915 | Calendar, Gmail, Photos | Calendar + Photos | Critical | mail.google.com/, photoslibrary.readonly, calendar.events.freebusy |
| SC-0921 | Cloud, Forms, Photos | Forms + Photos | High | photoslibrary.readonly, cloud-platform, forms.body |
| SC-0926 | Calendar, Contacts, Forms, Gmail, Photos | Calendar + Photos; Forms + Photos | Critical | photoslibrary, gmail.labels, calendar.calendarlist.readonly, forms.currentonly, user.addresses.read |
| SC-0930 | Calendar, Drive, Fitness, Photos | Calendar + Photos | High | drive.metadata, photoslibrary, fitness.body.read, calendar.calendars.readonly |
| SC-0935 | Contacts, Drive, Photos, YouTube | Contacts + YouTube | High | contacts.other.readonly, drive.scripts, youtube.readonly, photoslibrary.readonly, drive.activity.readonly |
| SC-0967 | Chat, Forms, Identity, Photos | Forms + Photos | High | profile, chat.spaces, forms.currentonly, photoslibrary.readonly.appcreateddata |
| SC-0975 | Contacts, Sheets, YouTube | Contacts + YouTube | High | user.organization.read, youtubepartner, spreadsheets |
| SC-0979 | Contacts, Forms, Gmail, Photos | Forms + Photos | High | photoslibrary.readonly.appcreateddata, user.emails.read, gmail.settings.sharing, forms.body.readonly |

#### Strategy H: Base Scope Combinations With Random Scope Addition (8 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-1177 | Drive, Identity, Keep, YouTube | Keep + YouTube | Critical | openid, profile, email, youtube, drive.file, keep.readonly |
| SC-1185 | Chat, Contacts, Identity, YouTube | Contacts + YouTube | Critical | openid, profile, email, chat.messages, contacts.readonly, youtube |
| SC-1186 | Calendar, Docs, Identity, Photos, Sheets, Slides | Calendar + Photos | High | openid, profile, email, presentations.readonly, documents.readonly, photoslibrary.readonly, spreadsheets.readonly, calendar.settings.readonly |
| SC-1200 | Docs, Drive, Forms, Identity, YouTube | Forms + YouTube | High | openid, profile, email, documents, forms.body, drive.file, youtube |
| SC-1205 | Contacts, Drive, Identity, YouTube | Contacts + YouTube | Critical | openid, profile, email, drive.readonly, youtube.upload, contacts |
| SC-1250 | Calendar, Contacts, Gmail, Photos | Calendar + Photos | Critical | gmail.readonly, contacts.readonly, calendar.calendars.readonly, photoslibrary.appendonly |
| SC-1255 | Calendar, Drive, Photos, Sheets | Calendar + Photos | Critical | drive, calendar, spreadsheets, photoslibrary |
| SC-1268 | Blogger, Classroom, Gmail, Sheets | Blogger + Classroom | Critical | classroom.coursework.students, spreadsheets, gmail.send, blogger |

#### Strategy J: Bool Switching of Medium Risk Combinations (1 row)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0965 | Blogger, Forms, YouTube | Blogger + Forms; Forms + YouTube | High | youtube, blogger.readonly, forms |

### T6 — Incoherent productivity / PIM pairing

**1 row removed.**

Workspace productivity pairings that survive every rule above but still describe no plausible application: the two services share neither a data flow nor a user task.

#### Strategy F: Randomly Generated Scope Combinations (1 row)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0862 | Calendar, Docs, Forms, Gmail, Keep | Forms + Keep | Critical | calendar.calendarlist, gmail.insert, keep.readonly, forms, documents.readonly |

---

## 5. Retained: T1 health / fitness combinations

These 53 rows were flagged by the plausibility filter and are **not removed**, per §2.4. They stay in the filtered dataset with their original risk labels unchanged.

| Generation method | T1 rows retained |
|---|---:|
| Strategy F: Randomly Generated Scope Combinations | 20 |
| Strategy B: Addition (student_gen) | 18 |
| Strategy B: Addition (github manifest) | 6 |
| Strategy H: Base Scope Combinations With Random Scope Addition | 4 |
| Strategy C: Removal | 3 |
| Strategy A: Boolean Switching | 1 |
| Student Created | 1 |
| **All** | **53** |

### 5.1 T1 rows that also break a non-health pairing

Seven retained rows contain a second implausible pairing that would, on its own, have placed them in T2–T5. They are retained anyway: the health scope dominates the interpretation of the request, and removing them would delete the pattern the exemption exists to preserve. They are listed here so the decision is auditable, and so they can be revisited if the exemption is later narrowed.

| SC ID | Generation method | Non-health pairing(s) | All flagged pairings |
|---|---|---|---|
| SC-0345 | Strategy B: Addition (student_gen) | Analytics + Contacts | Analytics + Contacts; Analytics + Fitness; Contacts + Fitness |
| SC-0387 | Strategy B: Addition (student_gen) | Chat + Firebase | Chat + Firebase; Chat + Fitness; Firebase + Fitness |
| SC-0931 | Strategy F: Randomly Generated Scope Combinations | Admin + YouTube | Admin + Fitness; Admin + YouTube; Fitness + YouTube |
| SC-0953 | Strategy F: Randomly Generated Scope Combinations | Analytics + Photos | Analytics + Fitness; Analytics + Photos |
| SC-0983 | Strategy F: Randomly Generated Scope Combinations | Calendar + Cloud Storage | Calendar + Cloud Storage; Cloud Storage + Fitness |
| SC-0995 | Strategy F: Randomly Generated Scope Combinations | Calendar + Photos | Calendar + Photos; Contacts + Fitness |
| SC-1201 | Strategy H: Base Scope Combinations With Random Scope Addition | Chat + Firebase | Chat + Firebase; Chat + Fitness; Firebase + Fitness |

### 5.2 T1 rows by generation method

**53 rows retained.**

Google Fitness scopes carry health data (activity, sleep, heart rate, blood glucose, blood pressure, body metrics) and are governed by Google's separate health-data policy, which restricts the fitness APIs to apps whose function is health and wellness. The curated plausibility list therefore admits Fitness only alongside services a fitness app genuinely needs — Drive, Photos, Sheets, Forms, Keep and Apps Script — to which this analysis adds Calendar and Tasks for training-plan scheduling. Every combination below pairs health data with a mailbox, a directory, a chat product, a cloud console or a media service, none of which a wellness app can justify under the same policy. **That is the reason they are kept.** Each one models a client requesting health data it has no functional claim to, alongside a service capable of moving that data elsewhere — the structure of a health-data acquisition attack. The 'Implausible pairing(s)' column is retained below as a record of why the row was flagged; it is no longer a removal justification.

##### Strategy A: Boolean Switching (1 row)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0130 | Firebase, Fitness, Identity | Firebase + Fitness | High | openid, profile, email, firebase, fitness.blood_glucose.read |

##### Strategy B: Addition (github manifest) (6 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0217 | Calendar, Contacts, Fitness, Gmail | Contacts + Fitness; Fitness + Gmail | Critical | gmail.send, gmail.readonly, contacts.readonly, calendar.events, fitness.activity.read |
| SC-0222 | Calendar, Contacts, Drive, Fitness, Gmail | Contacts + Fitness; Fitness + Gmail | Critical | contacts, gmail.send, calendar.events, drive.file, fitness.activity.read |
| SC-0244 | Drive, Fitness, Gmail, Sheets | Fitness + Gmail | Critical | spreadsheets, gmail.send, drive.file, fitness.activity.read |
| SC-0251 | Apps Script, Drive, Fitness, Gmail, Sheets | Fitness + Gmail | Critical | script.projects, drive, spreadsheets, gmail.send, fitness.activity.read |
| SC-0303 | Cloud, Compute, Fitness | Cloud + Fitness; Compute + Fitness | Critical | cloud-platform, compute, fitness.activity.read |
| SC-0305 | BigQuery, Cloud Storage, Fitness | BigQuery + Fitness; Cloud Storage + Fitness | High | devstorage.read_write, bigquery, fitness.activity.read |

##### Strategy B: Addition (student_gen) (18 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0310 | Contacts, Fitness, Identity, Sheets | Contacts + Fitness | Critical | openid, profile, email, fitness.activity.read, fitness.body.read, spreadsheets, contacts.readonly |
| SC-0311 | Fitness, Gmail, Identity, Sheets | Fitness + Gmail | Critical | openid, profile, email, fitness.activity.read, fitness.body.read, spreadsheets, gmail.send |
| SC-0314 | Drive, Fitness, Identity, YouTube | Fitness + YouTube | High | openid, profile, email, youtube, drive.file, fitness.activity.read |
| SC-0317 | Contacts, Fitness, Gmail, Identity | Contacts + Fitness; Fitness + Gmail | Critical | openid, profile, email, contacts.readonly, gmail.compose, fitness.activity.read |
| SC-0332 | Compute, Firebase, Fitness, Identity | Compute + Fitness; Firebase + Fitness | High | openid, profile, email, firebase, compute, fitness.activity.read |
| SC-0337 | Chat, Contacts, Fitness, Identity | Chat + Fitness; Contacts + Fitness | Critical | openid, profile, email, chat.messages, contacts.readonly, fitness.activity.read |
| SC-0345 | Analytics, Contacts, Fitness, Identity | Analytics + Contacts; Analytics + Fitness; Contacts + Fitness | High | openid, profile, email, userinfo.profile, analytics, user.addresses.read, fitness.activity.read |
| SC-0350 | BigQuery, Cloud Storage, Fitness | BigQuery + Fitness; Cloud Storage + Fitness | High | bigquery, devstorage.read_write, fitness.activity.read |
| SC-0364 | Chat, Drive, Fitness, Identity | Chat + Fitness | Critical | openid, profile, email, chat.messages, drive.readonly, fitness.activity.read |
| SC-0387 | Chat, Firebase, Fitness, Identity | Chat + Firebase; Chat + Fitness; Firebase + Fitness | Critical | openid, profile, email, firebase, fitness.blood_glucose.read, chat.messages |
| SC-0388 | Firebase, Fitness, Gmail, Identity | Firebase + Fitness; Fitness + Gmail | Critical | openid, profile, email, firebase, fitness.blood_glucose.read, gmail.send |
| SC-0389 | Contacts, Firebase, Fitness, Identity | Contacts + Fitness; Firebase + Fitness | Critical | openid, profile, email, firebase, fitness.blood_glucose.read, contacts.readonly |
| SC-0424 | Calendar, Chat, Fitness, Identity | Chat + Fitness | High | openid, profile, email, calendar.events.owned, chat.messages.readonly, fitness.activity.read |
| SC-0428 | BigQuery, Cloud Storage, Fitness, Sheets | BigQuery + Fitness; Cloud Storage + Fitness | Critical | bigquery, devstorage.read_write, spreadsheets, fitness.activity.read |
| SC-0430 | Admin, Fitness, Gmail, Identity | Admin + Fitness; Fitness + Gmail | Critical | openid, profile, email, gmail.send, admin.datatransfer, fitness.activity.read |
| SC-0433 | Drive, Fitness, Gmail, Identity | Fitness + Gmail | Critical | openid, profile, email, drive.activity.readonly, gmail.send, fitness.activity.read |
| SC-0447 | Calendar, Classroom, Fitness, Gmail, Identity | Classroom + Fitness; Fitness + Gmail | Critical | openid, profile, email, gmail.send, classroom.profile.emails, calendar.events.readonly, fitness.activity.read |
| SC-0457 | Chat, Fitness, Gmail, Identity, Photos | Chat + Fitness; Fitness + Gmail | High | openid, profile, email, photoslibrary.appendonly, chat.messages.readonly, gmail.addons.current.message.readonly, fitness.activity.read |

##### Strategy C: Removal (3 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0536 | Firebase, Fitness, Identity | Firebase + Fitness | High | openid, profile, firebase, fitness.blood_glucose.read |
| SC-0537 | Firebase, Fitness, Identity | Firebase + Fitness | High | profile, email, firebase, fitness.blood_glucose.read |
| SC-0539 | Firebase, Fitness, Identity | Firebase + Fitness | High | openid, email, firebase, fitness.blood_glucose.read |

##### Strategy F: Randomly Generated Scope Combinations (20 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0883 | Calendar, Classroom, Contacts, Fitness | Classroom + Fitness; Contacts + Fitness | High | calendar.app.created, fitness.activity.read, classroom.profile.emails, user.phonenumbers.read, calendar.readonly |
| SC-0884 | Firebase, Fitness, Gmail | Firebase + Fitness; Fitness + Gmail | Critical | mail.google.com/, fitness.location.read, firebase.messaging |
| SC-0885 | Chat, Fitness, Slides | Chat + Fitness | High | chat.memberships, fitness.blood_glucose.read, presentations.readonly |
| SC-0888 | Admin, Apps Script, Compute, Fitness, Identity | Admin + Fitness; Compute + Fitness | Critical | userinfo.email, fitness.blood_pressure.read, admin.directory.rolemanagement, script.projects.readonly, compute |
| SC-0906 | Cloud Storage, Drive, Fitness, Forms, Gmail | Cloud Storage + Fitness; Fitness + Gmail | Critical | forms.body, gmail.readonly, drive.readonly, devstorage.full_control, fitness.body.read |
| SC-0908 | Analytics, Fitness | Analytics + Fitness | Medium | fitness.activity.read, analytics.readonly, fitness.body.read |
| SC-0918 | Calendar, Chat, Fitness, Gmail | Chat + Fitness; Fitness + Gmail | Critical | calendar.events, gmail.readonly, fitness.blood_glucose.read, chat.delete |
| SC-0931 | Admin, Fitness, YouTube | Admin + Fitness; Admin + YouTube; Fitness + YouTube | Critical | fitness.blood_pressure.read, admin.datatransfer, fitness.sleep.read, admin.reports.audit.readonly, youtubepartner |
| SC-0933 | Fitness, Gmail, Identity, YouTube | Fitness + Gmail; Fitness + YouTube | Critical | mail.google.com/, fitness.activity.write, youtube.upload, openid |
| SC-0936 | Calendar, Contacts, Docs, Fitness, Gmail | Contacts + Fitness; Fitness + Gmail | Critical | fitness.blood_pressure.read, documents.readonly, user.phonenumbers.read, calendar.events.readonly, gmail.insert |
| SC-0953 | Analytics, Fitness, Identity, Photos | Analytics + Fitness; Analytics + Photos | High | fitness.sleep.read, profile, analytics, photoslibrary.appendonly |
| SC-0959 | Apps Script, Fitness, Gmail | Fitness + Gmail | High | gmail.insert, fitness.blood_pressure.read, script.deployments |
| SC-0960 | Calendar, Contacts, Drive, Fitness, Forms | Contacts + Fitness | High | user.phonenumbers.read, drive.photos.readonly, forms, calendar.acls.readonly, fitness.activity.write |
| SC-0973 | Calendar, Contacts, Fitness | Contacts + Fitness | High | user.organization.read, fitness.body.read, calendar.calendars |
| SC-0976 | Calendar, Fitness, Gmail | Fitness + Gmail | High | fitness.activity.write, gmail.addons.current.message.metadata, calendar.events |
| SC-0981 | Calendar, Drive, Fitness, Forms, Gmail | Fitness + Gmail | Critical | gmail.settings.sharing, calendar.freebusy, fitness.activity.write, drive.scripts, forms.body |
| SC-0983 | Calendar, Cloud Storage, Drive, Fitness, Identity | Calendar + Cloud Storage; Cloud Storage + Fitness | High | devstorage.read_write, fitness.blood_glucose.read, drive.appdata, calendar.acls, openid |
| SC-0989 | Contacts, Drive, Fitness | Contacts + Fitness | High | drive.appdata, contacts.readonly, fitness.blood_glucose.read |
| SC-0995 | Calendar, Contacts, Fitness, Photos | Calendar + Photos; Contacts + Fitness | Critical | fitness.location.read, calendar.acls.readonly, contacts, photoslibrary |
| SC-0997 | Admin, Calendar, Fitness, Forms | Admin + Fitness | High | forms.body.readonly, fitness.location.read, calendar.calendarlist.readonly, admin.reports.audit.readonly |

##### Strategy H: Base Scope Combinations With Random Scope Addition (4 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-1201 | Chat, Firebase, Fitness, Identity | Chat + Firebase; Chat + Fitness; Firebase + Fitness | Critical | openid, profile, email, firebase, fitness.blood_glucose.read, chat.delete |
| SC-1212 | Chat, Fitness, Gmail, Identity | Chat + Fitness; Fitness + Gmail | Critical | openid, profile, email, gmail.addons.current.message.readonly, chat.messages, fitness.body.read |
| SC-1232 | Fitness, Gmail | Fitness + Gmail | High | gmail.modify, gmail.settings.basic, fitness.activity.read |
| SC-1235 | Admin, Fitness | Admin + Fitness | Critical | admin.directory.user, admin.directory.group, admin.directory.domain, admin.datatransfer, fitness.location.read |

##### Student Created (1 row)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0026 | Firebase, Fitness, Identity | Firebase + Fitness | High | openid, profile, email, firebase, fitness.blood_glucose.read |


---

## 6. Removal list

The 137 combinations removed under the non-T1 justifications (T0, T2, T3, T4, T5, T6), in ascending SC order. Per-combination justifications are in Appendix D.

```
SC-0011
SC-0017
SC-0115
SC-0121
SC-0256
SC-0257
SC-0258
SC-0259
SC-0260
SC-0261
SC-0268
SC-0270
SC-0302
SC-0304
SC-0307
SC-0315
SC-0321
SC-0331
SC-0333
SC-0343
SC-0344
SC-0351
SC-0352
SC-0353
SC-0354
SC-0361
SC-0362
SC-0363
SC-0370
SC-0371
SC-0396
SC-0398
SC-0400
SC-0405
SC-0406
SC-0411
SC-0412
SC-0426
SC-0438
SC-0439
SC-0440
SC-0442
SC-0454
SC-0499
SC-0500
SC-0502
SC-0515
SC-0516
SC-0517
SC-0639
SC-0640
SC-0641
SC-0642
SC-0862
SC-0863
SC-0865
SC-0866
SC-0868
SC-0869
SC-0871
SC-0873
SC-0876
SC-0877
SC-0880
SC-0881
SC-0882
SC-0887
SC-0892
SC-0893
SC-0894
SC-0897
SC-0898
SC-0901
SC-0902
SC-0909
SC-0911
SC-0915
SC-0920
SC-0921
SC-0923
SC-0926
SC-0927
SC-0930
SC-0934
SC-0935
SC-0939
SC-0940
SC-0941
SC-0942
SC-0943
SC-0946
SC-0948
SC-0949
SC-0950
SC-0952
SC-0954
SC-0957
SC-0961
SC-0962
SC-0963
SC-0964
SC-0965
SC-0966
SC-0967
SC-0969
SC-0970
SC-0971
SC-0972
SC-0974
SC-0975
SC-0979
SC-0982
SC-0985
SC-0990
SC-0993
SC-0994
SC-0996
SC-0998
SC-0999
SC-1177
SC-1179
SC-1185
SC-1186
SC-1187
SC-1195
SC-1200
SC-1205
SC-1218
SC-1219
SC-1223
SC-1244
SC-1250
SC-1255
SC-1261
SC-1262
SC-1268
SC-1269
```

### 6.1 Same list, grouped by category

**T0 — Multi-domain sprawl with no coherent application archetype** (16 rows)

SC-0362, SC-0887, SC-0911, SC-0934, SC-0941, SC-0948, SC-0963, SC-0964, SC-0966, SC-0972, SC-0982, SC-0990, SC-0994, SC-0996, SC-0998, SC-1244

**T2 — Domain administration combined with a consumer or marketing service** (17 rows)

SC-0017, SC-0121, SC-0361, SC-0363, SC-0515, SC-0516, SC-0517, SC-0871, SC-0876, SC-0880, SC-0893, SC-0901, SC-0946, SC-0950, SC-0970, SC-0985, SC-1223

**T3 — Cloud / developer infrastructure combined with personal communication or PIM data** (43 rows)

SC-0260, SC-0261, SC-0302, SC-0304, SC-0307, SC-0321, SC-0331, SC-0333, SC-0351, SC-0352, SC-0353, SC-0354, SC-0396, SC-0398, SC-0426, SC-0438, SC-0439, SC-0440, SC-0442, SC-0863, SC-0865, SC-0866, SC-0877, SC-0892, SC-0894, SC-0898, SC-0902, SC-0920, SC-0927, SC-0939, SC-0943, SC-0949, SC-0961, SC-0962, SC-0969, SC-0971, SC-0974, SC-0999, SC-1179, SC-1218, SC-1219, SC-1262, SC-1269

**T4 — Marketing and monetization combined with personal data services** (32 rows)

SC-0011, SC-0115, SC-0256, SC-0257, SC-0258, SC-0259, SC-0268, SC-0270, SC-0343, SC-0344, SC-0370, SC-0371, SC-0405, SC-0406, SC-0454, SC-0499, SC-0500, SC-0502, SC-0868, SC-0873, SC-0882, SC-0909, SC-0923, SC-0940, SC-0942, SC-0952, SC-0954, SC-0957, SC-0993, SC-1187, SC-1195, SC-1261

**T5 — Consumer media combined with an unrelated productivity or enterprise service** (28 rows)

SC-0315, SC-0400, SC-0411, SC-0412, SC-0639, SC-0640, SC-0641, SC-0642, SC-0869, SC-0881, SC-0897, SC-0915, SC-0921, SC-0926, SC-0930, SC-0935, SC-0965, SC-0967, SC-0975, SC-0979, SC-1177, SC-1185, SC-1186, SC-1200, SC-1205, SC-1250, SC-1255, SC-1268

**T6 — Incoherent productivity / PIM pairing** (1 rows)

SC-0862


---

## Appendix A — Archetype gaps added to the plausibility whitelist

Pairs absent from `plausable_cross_patterns` that this analysis nonetheless treats as plausible, each with the application archetype that justifies it. Without these, the filter would remove roughly 200 further rows that describe perfectly ordinary applications.

| Service pair | Archetype |
|---|---|
| Admin + Calendar | Workspace admin console (resource calendars) |
| Admin + Chat | Workspace admin console (Chat space management) |
| Admin + Forms | Workspace admin console (org-wide forms) |
| Admin + Groups | directory and group administration |
| Admin + Tasks | Workspace admin console (suite-wide provisioning) |
| Apps Script + Forms | Forms automation via Apps Script |
| Blogger + Docs | draft-in-Docs, publish-to-Blogger workflow |
| Blogger + Sheets | editorial calendar / post scheduling |
| Blogger + Slides | draft-in-Slides, publish-to-Blogger workflow |
| Blogger + YouTube | creator cross-posting |
| Calendar + Drive | meeting-notes / project management (files attached to events) |
| Calendar + Fitness | training-plan scheduling |
| Calendar + Forms | booking and event-registration forms |
| Calendar + Groups | group calendars and invitations |
| Chat + Gmail | Workspace assistant / notification relay |
| Chat + YouTube | media sharing bot (mirrors curated Chat+Photos) |
| Classroom + Groups | class-group synchronisation |
| Classroom + YouTube | instructional video in coursework |
| Drive + Groups | group-based file sharing |
| Drive + Tasks | task manager attaching reference files |
| Fitness + Tasks | training-goal tracking |
| Forms + Tasks | form submission raises a task |
| Gmail + Groups | mailing-list management |
| Gmail + Keep | save-email-as-note (Keep side panel) |
| Gmail + Tasks | email-to-task capture (Todoist, Asana style) |
| Groups + Sheets | group-membership export / audit |
| Keep + Photos | notes with attached images |

## Appendix B — Inventory of implausible pairings

Every service pairing that triggered a removal, with the number of removed rows it appears in. Counts cover the 137 removed rows only; pairings that appear solely in retained T1 rows are absent, and Fitness pairings that remain do so through T0 sprawl rows. Useful as a constraint list if the generator is rebuilt: forbidding these pairs at generation time removes the need for this filter — with the deliberate exception of Fitness pairings, which the generator should keep producing as attack examples.

| Implausible pairing | Rows |
|---|---:|
| Analytics + Contacts | 16 |
| Contacts + YouTube | 15 |
| Admin + Analytics | 14 |
| Analytics + Calendar | 12 |
| Calendar + Photos | 11 |
| Analytics + Tasks | 9 |
| BigQuery + Chat | 9 |
| Calendar + Cloud Storage | 9 |
| Calendar + Firebase | 7 |
| Chat + Cloud Storage | 7 |
| Analytics + Chat | 6 |
| Calendar + Compute | 6 |
| Analytics + Fitness | 5 |
| Firebase + Tasks | 5 |
| Admin + Fitness | 4 |
| Admin + Photos | 4 |
| Analytics + Forms | 4 |
| Chat + Firebase | 4 |
| Compute + Tasks | 4 |
| Forms + Photos | 4 |
| AdSense + Contacts | 3 |
| Admin + YouTube | 3 |
| Analytics + Classroom | 3 |
| BigQuery + Tasks | 3 |
| Classroom + Fitness | 3 |
| Cloud Storage + Tasks | 3 |
| Compute + Fitness | 3 |
| Firebase + Keep | 3 |
| Fitness + Gmail | 3 |
| AdSense + Calendar | 2 |
| AdSense + Chat | 2 |
| AdSense + Forms | 2 |
| AdSense + Tasks | 2 |
| Admin + Blogger | 2 |
| BigQuery + Calendar | 2 |
| Blogger + Calendar | 2 |
| Blogger + Forms | 2 |
| Calendar + Cloud | 2 |
| Chat + Compute | 2 |
| Forms + Keep | 2 |
| Forms + YouTube | 2 |
| AdSense + Admin | 1 |
| Analytics + Keep | 1 |
| Analytics + Photos | 1 |
| BigQuery + Fitness | 1 |
| BigQuery + Keep | 1 |
| Blogger + Chat | 1 |
| Blogger + Classroom | 1 |
| Blogger + Cloud | 1 |
| Blogger + Cloud Storage | 1 |
| Blogger + Compute | 1 |
| Blogger + Contacts | 1 |
| Blogger + Firebase | 1 |
| Blogger + Tasks | 1 |
| Chat + Cloud | 1 |
| Chat + Fitness | 1 |
| Classroom + Photos | 1 |
| Cloud + Tasks | 1 |
| Cloud Storage + Fitness | 1 |
| Compute + Keep | 1 |
| Firebase + Fitness | 1 |
| Fitness + Groups | 1 |
| Keep + YouTube | 1 |

## Appendix C — Reproducibility

The decision is deterministic and depends on no random state. Inputs are the dataset, the curated `plausable_cross_patterns` list from the dataset-creation notebook, the family definitions in §2.2 rule 4, and the archetype list in Appendix A. Files produced alongside this report:

- `scope_guard_dataset008_keep_remove_decisions.csv` — every row with its KEEP/REMOVE decision, removal category, offending pairs and resolved services. Rows in category T1 carry the flag but a KEEP decision.
- `scope_guard_dataset008_filtered.csv` — the dataset with the 137 removed rows dropped, columns otherwise unchanged. The 53 T1 rows are present.

The T1 exemption is applied after categorisation and changes no upstream step, so the earlier all-190 filter is reproducible from the same inputs by dropping the exemption in §2.4.

## Appendix D — Removal justification by combination

One row per removed combination: 137 in total. The justification names the category and the specific service pairing(s) that triggered it. T1 rows do not appear here — they are retained (§5).

| SC ID | Category | Justification for removal |
|---|---|---|
| SC-0011 | T4 | Marketing and monetization combined with personal data services — Analytics + Contacts |
| SC-0017 | T2 | Domain administration combined with a consumer or marketing service — Admin + Analytics |
| SC-0115 | T4 | Marketing and monetization combined with personal data services — Analytics + Contacts |
| SC-0121 | T2 | Domain administration combined with a consumer or marketing service — Admin + Analytics |
| SC-0256 | T4 | Marketing and monetization combined with personal data services — Analytics + Tasks |
| SC-0257 | T4 | Marketing and monetization combined with personal data services — Analytics + Contacts |
| SC-0258 | T4 | Marketing and monetization combined with personal data services — Analytics + Calendar |
| SC-0259 | T4 | Marketing and monetization combined with personal data services — Analytics + Contacts |
| SC-0260 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Analytics + Chat; BigQuery + Chat |
| SC-0261 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Analytics + Tasks; BigQuery + Tasks |
| SC-0268 | T4 | Marketing and monetization combined with personal data services — Analytics + Tasks |
| SC-0270 | T4 | Marketing and monetization combined with personal data services — Analytics + Contacts; Contacts + YouTube |
| SC-0302 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Cloud + Tasks; Compute + Tasks |
| SC-0304 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — BigQuery + Chat; Chat + Cloud Storage |
| SC-0307 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Calendar + Cloud; Calendar + Compute |
| SC-0315 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Contacts + YouTube |
| SC-0321 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Cloud Storage + Tasks |
| SC-0331 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Compute + Tasks; Firebase + Tasks |
| SC-0333 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Calendar + Compute; Calendar + Firebase |
| SC-0343 | T4 | Marketing and monetization combined with personal data services — Analytics + Calendar; Analytics + Contacts |
| SC-0344 | T4 | Marketing and monetization combined with personal data services — Analytics + Contacts |
| SC-0351 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — BigQuery + Chat; Chat + Cloud Storage |
| SC-0352 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Calendar + Firebase |
| SC-0353 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Firebase + Tasks |
| SC-0354 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Chat + Firebase |
| SC-0361 | T2 | Domain administration combined with a consumer or marketing service — Admin + Analytics |
| SC-0362 | T0 | Multi-domain sprawl with no coherent application archetype — Admin + Analytics; Admin + Fitness; Analytics + Fitness |
| SC-0363 | T2 | Domain administration combined with a consumer or marketing service — Admin + Analytics; Analytics + Calendar |
| SC-0370 | T4 | Marketing and monetization combined with personal data services — Analytics + Calendar; Blogger + Calendar |
| SC-0371 | T4 | Marketing and monetization combined with personal data services — Analytics + Contacts; Blogger + Contacts |
| SC-0396 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — BigQuery + Chat |
| SC-0398 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — BigQuery + Tasks |
| SC-0400 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Contacts + YouTube |
| SC-0405 | T4 | Marketing and monetization combined with personal data services — Analytics + Chat |
| SC-0406 | T4 | Marketing and monetization combined with personal data services — Analytics + Calendar |
| SC-0411 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Blogger + Tasks |
| SC-0412 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Blogger + Calendar |
| SC-0426 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — BigQuery + Chat; Chat + Cloud Storage |
| SC-0438 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Calendar + Compute; Calendar + Firebase |
| SC-0439 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Compute + Tasks; Firebase + Tasks |
| SC-0440 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Chat + Compute; Chat + Firebase |
| SC-0442 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Analytics + Tasks; Firebase + Tasks |
| SC-0454 | T4 | Marketing and monetization combined with personal data services — AdSense + Tasks; Analytics + Tasks |
| SC-0499 | T4 | Marketing and monetization combined with personal data services — Analytics + Contacts |
| SC-0500 | T4 | Marketing and monetization combined with personal data services — Analytics + Contacts |
| SC-0502 | T4 | Marketing and monetization combined with personal data services — Analytics + Contacts |
| SC-0515 | T2 | Domain administration combined with a consumer or marketing service — Admin + Analytics |
| SC-0516 | T2 | Domain administration combined with a consumer or marketing service — Admin + Analytics |
| SC-0517 | T2 | Domain administration combined with a consumer or marketing service — Admin + Analytics |
| SC-0639 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Contacts + YouTube |
| SC-0640 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Calendar + Photos; Contacts + YouTube |
| SC-0641 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Contacts + YouTube |
| SC-0642 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Calendar + Photos |
| SC-0862 | T6 | Incoherent productivity / PIM pairing — Forms + Keep |
| SC-0863 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Calendar + Cloud Storage |
| SC-0865 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Blogger + Cloud Storage |
| SC-0866 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Calendar + Cloud Storage; Calendar + Photos |
| SC-0868 | T4 | Marketing and monetization combined with personal data services — Analytics + Calendar; Analytics + Tasks |
| SC-0869 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Contacts + YouTube |
| SC-0871 | T2 | Domain administration combined with a consumer or marketing service — Admin + Analytics; Admin + YouTube |
| SC-0873 | T4 | Marketing and monetization combined with personal data services — Analytics + Contacts; Analytics + Forms |
| SC-0876 | T2 | Domain administration combined with a consumer or marketing service — Admin + Analytics; Analytics + Classroom |
| SC-0877 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Calendar + Cloud Storage; Cloud Storage + Tasks |
| SC-0880 | T2 | Domain administration combined with a consumer or marketing service — Admin + Analytics; Analytics + Forms |
| SC-0881 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Calendar + Photos |
| SC-0882 | T4 | Marketing and monetization combined with personal data services — Analytics + Tasks |
| SC-0887 | T0 | Multi-domain sprawl with no coherent application archetype — AdSense + Calendar; AdSense + Contacts; AdSense + Tasks; Calendar + Cloud Storage; Cloud Storage + Tasks |
| SC-0892 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Calendar + Firebase |
| SC-0893 | T2 | Domain administration combined with a consumer or marketing service — AdSense + Admin; AdSense + Contacts |
| SC-0894 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — BigQuery + Chat; Chat + Cloud Storage |
| SC-0897 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Contacts + YouTube |
| SC-0898 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Calendar + Compute |
| SC-0901 | T2 | Domain administration combined with a consumer or marketing service — Admin + Analytics; Analytics + Tasks |
| SC-0902 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Calendar + Firebase; Contacts + YouTube |
| SC-0909 | T4 | Marketing and monetization combined with personal data services — Analytics + Calendar |
| SC-0911 | T0 | Multi-domain sprawl with no coherent application archetype — Calendar + Compute; Compute + Fitness; Fitness + Gmail |
| SC-0915 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Calendar + Photos |
| SC-0920 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Calendar + Cloud |
| SC-0921 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Forms + Photos |
| SC-0923 | T4 | Marketing and monetization combined with personal data services — Analytics + Chat |
| SC-0926 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Calendar + Photos; Forms + Photos |
| SC-0927 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — BigQuery + Calendar; BigQuery + Chat |
| SC-0930 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Calendar + Photos |
| SC-0934 | T0 | Multi-domain sprawl with no coherent application archetype — Analytics + Classroom; Analytics + Fitness; Classroom + Fitness; Compute + Fitness |
| SC-0935 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Contacts + YouTube |
| SC-0939 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Calendar + Cloud Storage |
| SC-0940 | T4 | Marketing and monetization combined with personal data services — Analytics + Calendar; Analytics + Forms |
| SC-0941 | T0 | Multi-domain sprawl with no coherent application archetype — Classroom + Fitness; Cloud Storage + Fitness; Compute + Fitness |
| SC-0942 | T4 | Marketing and monetization combined with personal data services — AdSense + Forms; Blogger + Forms |
| SC-0943 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Compute + Keep; Firebase + Keep |
| SC-0946 | T2 | Domain administration combined with a consumer or marketing service — Admin + Photos |
| SC-0948 | T0 | Multi-domain sprawl with no coherent application archetype — Admin + Fitness; Chat + Fitness; Fitness + Gmail; Fitness + Groups |
| SC-0949 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — BigQuery + Keep; Firebase + Keep |
| SC-0950 | T2 | Domain administration combined with a consumer or marketing service — Admin + Photos |
| SC-0952 | T4 | Marketing and monetization combined with personal data services — Analytics + Contacts |
| SC-0954 | T4 | Marketing and monetization combined with personal data services — AdSense + Forms |
| SC-0957 | T4 | Marketing and monetization combined with personal data services — AdSense + Calendar |
| SC-0961 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Chat + Cloud Storage |
| SC-0962 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Calendar + Cloud Storage; Calendar + Firebase |
| SC-0963 | T0 | Multi-domain sprawl with no coherent application archetype — Analytics + Calendar; Analytics + Contacts; BigQuery + Calendar |
| SC-0964 | T0 | Multi-domain sprawl with no coherent application archetype — Analytics + Fitness; Analytics + Tasks; BigQuery + Fitness; BigQuery + Tasks; Firebase + Fitness; Firebase + Tasks |
| SC-0965 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Blogger + Forms; Forms + YouTube |
| SC-0966 | T0 | Multi-domain sprawl with no coherent application archetype — Admin + Fitness; Admin + Photos; Classroom + Fitness; Classroom + Photos; Fitness + Gmail |
| SC-0967 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Forms + Photos |
| SC-0969 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Blogger + Firebase |
| SC-0970 | T2 | Domain administration combined with a consumer or marketing service — Admin + YouTube |
| SC-0971 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — AdSense + Chat; Chat + Cloud Storage |
| SC-0972 | T0 | Multi-domain sprawl with no coherent application archetype — Analytics + Fitness; Analytics + Forms; Analytics + Keep; Forms + Keep |
| SC-0974 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Firebase + Keep |
| SC-0975 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Contacts + YouTube |
| SC-0979 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Forms + Photos |
| SC-0982 | T0 | Multi-domain sprawl with no coherent application archetype — Admin + Blogger; Blogger + Cloud; Blogger + Compute |
| SC-0985 | T2 | Domain administration combined with a consumer or marketing service — Admin + Blogger |
| SC-0990 | T0 | Multi-domain sprawl with no coherent application archetype — Admin + Analytics; Admin + Fitness; Analytics + Calendar; Analytics + Fitness |
| SC-0993 | T4 | Marketing and monetization combined with personal data services — AdSense + Contacts; Contacts + YouTube |
| SC-0994 | T0 | Multi-domain sprawl with no coherent application archetype — AdSense + Chat; BigQuery + Chat; Chat + Firebase |
| SC-0996 | T0 | Multi-domain sprawl with no coherent application archetype — Admin + Analytics; Admin + YouTube; Analytics + Classroom |
| SC-0998 | T0 | Multi-domain sprawl with no coherent application archetype — Analytics + Chat; Analytics + Contacts; Chat + Cloud |
| SC-0999 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Calendar + Compute; Compute + Tasks |
| SC-1177 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Keep + YouTube |
| SC-1179 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Calendar + Cloud Storage |
| SC-1185 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Contacts + YouTube |
| SC-1186 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Calendar + Photos |
| SC-1187 | T4 | Marketing and monetization combined with personal data services — Analytics + Contacts; Analytics + Photos |
| SC-1195 | T4 | Marketing and monetization combined with personal data services — Analytics + Chat; Blogger + Chat |
| SC-1200 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Forms + YouTube |
| SC-1205 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Contacts + YouTube |
| SC-1218 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Chat + Compute; Chat + Firebase |
| SC-1219 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Analytics + Calendar; Calendar + Firebase |
| SC-1223 | T2 | Domain administration combined with a consumer or marketing service — Admin + Photos |
| SC-1244 | T0 | Multi-domain sprawl with no coherent application archetype — Calendar + Cloud Storage; Calendar + Photos; Contacts + YouTube |
| SC-1250 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Calendar + Photos |
| SC-1255 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Calendar + Photos |
| SC-1261 | T4 | Marketing and monetization combined with personal data services — Analytics + Calendar |
| SC-1262 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Analytics + Chat; BigQuery + Chat |
| SC-1268 | T5 | Consumer media combined with an unrelated productivity or enterprise service — Blogger + Classroom |
| SC-1269 | T3 | Cloud / developer infrastructure combined with personal communication or PIM data — Calendar + Cloud Storage; Chat + Cloud Storage |

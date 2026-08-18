# Removing Unrealistic Scope Combinations from `scope_guard_dataset008.csv`

**Basis for removal:** implausible *service* combinations. Health and fitness pairings are **not** a removal category and are not grounds for removal; they are identified in §5.
**Rows examined:** 1845 (every row in the dataset).  
**Rows flagged as implausible:** 236. **Rows carrying a health/fitness pairing:** 71 (§5).
**Decision:** KEEP 1664 | REMOVE 181 (9.8% of the dataset).

> **Revision note.** This report supersedes the version written against the earlier build of the dataset. Two things changed. First, the dataset itself was regenerated after the duplicate-registry fix in the creation notebook, so every count, row id and per-strategy figure below is recomputed from scratch; nothing is carried over. Second, **health/fitness combinations no longer form a category.** The previous report filed them as T1 and then exempted that category from removal, which meant the taxonomy contained one entry that was defined by its data type rather than by an implausible pairing, and that was never removed. Fitness pairings are now excluded from the plausibility test itself (§2.4), so they neither trigger a flag nor occupy a category. The categories have been renumbered accordingly: what was T0 (sprawl) is now **T1**, and T2–T6 keep their previous meanings and numbers.

REMOVE decisions are itemised in §4. Rows containing health data are itemised in §5, which is a disclosure section, not a category. The complete keep/remove decision for all rows is machine-readable in `scope_guard_dataset008_keep_remove_decisions.csv`, and `scope_guard_dataset008_filtered.csv` holds the surviving rows.

---

## 1. Why this filter is needed

The dataset is built from three attested seed sets and then expanded by ten generation strategies. Four of those strategies (B, C, F, H) draw scopes uniformly at random, either from the full catalog or from a pool of commonly requested scopes, and attach them to an existing combination without any check on whether the resulting service mix corresponds to a real application. The generator already encodes a notion of which service pairs make sense — the `plausable_cross_patterns` list that drives Strategies E and G — but that constraint is never applied to the other strategies or back onto the seed sets.

The consequence is a class of rows whose risk label is driven by breadth and sensitivity that no consent screen would ever display. A model trained on them learns that Analytics plus Contacts plus Compute is a Critical request, when the useful discrimination is between requests a user might actually be asked to approve — or, for the attack classes the model does need to see, between those and requests that only *look* broad. These rows inflate the Critical and High classes specifically, since implausible mixes are almost always broad and cross-service.

One finding is new to this build. **Strategy G is no longer clean.** It seeds from the curated pair list and then adds a random *common* scope, and that addition is not re-checked against the list, so a plausible cross-service pair acquires a third service that pairs with neither. 29 Strategy G rows are removed below, against none in the previous build, where the strategy added its scope differently. Strategies D, E and I remain clean by construction.

## 2. Method

### 2.1 Service resolution

Each scope URL was mapped back to its catalog service. The mapping was validated by reproducing two columns the dataset already carries: predicted service counts matched `cross_service_breadth` and predicted maximum sensitivity matched `data_sensitivity` for all 1845 rows (0 mismatches). Note that the People API scopes (`user.*.read`, `directory.readonly`) resolve to **Contacts**, not Identity or Admin.

### 2.2 Plausibility of a service pair

A combination is assessed as the set of unordered service pairs it induces. A pair is treated as **plausible** if any of the following hold:

1. **Curated list.** The pair appears in the generator's own `plausable_cross_patterns` list (176 distinct unordered pairs). Reusing the project's existing judgement keeps the filter consistent with the data it is filtering.
2. **Identity is universal.** `openid`, `email`, `profile` and the profile scopes accompany every OAuth application, so Identity pairs with anything.
3. **Single service.** Both scopes belong to one service.
4. **Family closure.** Docs/Sheets/Slides, the five GCP services (Cloud, Compute, BigQuery, Cloud Storage, Firebase), and Analytics/AdSense are sibling products. If the curated list accepts any member of one family with any member of another, the whole family pair is accepted. This repairs asymmetries in the curated list — it admits Sheets + Cloud Storage but not Docs + Cloud Storage, and Admin + BigQuery but not Admin + Cloud Storage — that are omissions rather than judgements.
5. **Named archetype gap.** The pair appears in the list in Appendix A: pairs the curated list omits but that map onto a documented application archetype (Calendar + Drive for meeting-notes tooling, Gmail + Tasks for email-to-task capture, and so on). Each entry names the archetype that justifies it.
6. **Health exclusion.** Either service is Fitness — see §2.4.

A combination is **flagged if any one of its pairs is implausible**, and kept otherwise. Flagged rows are removed unless the exemption in §2.3 applies. The rule is deliberately pair-local: one indefensible pairing is enough to make the whole request unrepresentable, and requiring several would keep three-service rows whose single bad pair is the only thing driving their breadth score.

### 2.3 Exemption for attested combinations

Rows sourced from **Published Attack Patterns** and **Github Manifest Combinations** are exempt. These are empirically observed — real client manifests and documented incident write-ups — so plausibility-by-archetype does not apply to them; a deliberately over-broad request is the phenomenon being modelled, not noise. The exemption extends to rows carrying an identical scope set to an attested seed, which covers the boolean-switched copies made by Strategy A. Derived rows that *add* or *remove* scopes are not exempt, because the derivation is synthetic.

In this build the exemption is load-bearing for 2 rows:

| SC ID | Source | Pairing(s) that would otherwise remove it | Risk label |
|---|---|---|---|
| SC-0070 | Published Attack Patterns | Calendar + Photos; Contacts + YouTube | Critical |
| SC-0172 | Strategy A: Boolean Switching | Calendar + Photos; Contacts + YouTube | Critical |

Student Created rows are **not** exempt: they are hand-written hypotheticals, and 2 of them fail the filter.

### 2.4 Health and fitness data is not a plausibility signal

Any pair involving **Fitness** is excluded from the plausibility test. It cannot flag a row, it cannot remove a row, and it does not count toward the sprawl threshold in T1.

The reasoning is that the plausibility argument against health pairings is an argument about *legitimate* applications: no wellness app can justify a mailbox, a directory, a chat product, a cloud console or a media service under Google's health-data policy. That is exactly why the combination is worth keeping. An OAuth request of this shape is the signature of a malicious health-data acquisition attempt — health scopes requested by a client with no health function, alongside a channel capable of moving the data off-platform — and a model trained to score consent screens should see it labelled at the top of the scale rather than never see it at all.

The previous report reached the same conclusion by a different route: it defined a category for these rows and then exempted the whole category from removal. That is equivalent to not having the category, and it had two costs. It put an entry in the taxonomy that was defined by data type rather than by an implausible pairing, and it gave the health rule priority over T2–T5, so a row that broke a genuine non-health pairing *and* happened to contain a Fitness scope was retained on the strength of the Fitness scope alone. Excluding Fitness from the test instead means each row is judged on the pairings that remain, which is the same treatment every other row gets.

The consequence is visible and is itemised in §5.2: 18 rows containing health data are removed here because of a pairing that has nothing to do with health. Under the previous rule they would have been retained. If you want the old behaviour, §5.2 is the exact list to add back.

### 2.5 Removal categories

Every flagged row is assigned to exactly one category, by the highest-priority violation it contains. Priority runs T1 → T6, so a row breaking three or more pairings is filed as sprawl (T1) regardless of content, and a row breaking both an administration pairing and a media pairing is filed under T2.

| Code | Category | Rows | Decision |
|---|---|---:|---|
| T1 | Multi-domain sprawl with no coherent application archetype | 11 | Remove |
| T2 | Domain administration combined with a consumer or marketing service | 22 | Remove |
| T3 | Cloud / developer infrastructure combined with personal communication or PIM data | 67 | Remove |
| T4 | Marketing and monetization combined with personal data services | 42 | Remove |
| T5 | Consumer media combined with an unrelated productivity or enterprise service | 38 | Remove |
| T6 | Incoherent productivity / PIM pairing | 1 | Remove |
|  | **Total removed** | **181** |  |

Health and fitness rows do not appear in this table. They are not a category; see §2.4 and §5.

## 3. Summary of removals

### 3.1 By generation method

| Generation method | Rows in dataset | Health rows kept | Removed | % removed |
|---|---:|---:|---:|---:|
| Strategy I: Low Sensitivity Service Scope Combinations Generation | 448 | 0 | 0 | 0.0% |
| Strategy C: Removal | 199 | 3 | 10 | 5.0% |
| Strategy G: Plausable Cross Scope Combinations With Random Common Scope Addition | 171 | 4 | 29 | 17.0% |
| Strategy J: Bool Switching of Medium Risk Combinations | 163 | 0 | 3 | 1.8% |
| Strategy E: Plausable Cross Scope Combinations | 154 | 0 | 0 | 0.0% |
| Strategy F: Randomly Generated Scope Combinations | 151 | 19 | 76 | 50.3% |
| Strategy B: Addition (student_gen) | 146 | 16 | 30 | 20.5% |
| Strategy A: Boolean Switching | 101 | 1 | 2 | 2.0% |
| Strategy H: Base Scope Combinations With Random Scope Addition | 99 | 3 | 18 | 18.2% |
| Strategy B: Addition (github manifest) | 96 | 6 | 11 | 11.5% |
| Student Created | 50 | 1 | 2 | 4.0% |
| Github Manifest Combinations | 32 | 0 | 0 | 0.0% |
| Published Attack Patterns | 21 | 0 | 0 | 0.0% |
| Strategy D: Within Service Combinations | 14 | 0 | 0 | 0.0% |
| **All** | **1845** | **53** | **181** | **9.8%** |

The concentration is where the generator applies no plausibility constraint. Strategy F (uniform random sampling over the whole catalog) loses the largest share, followed by the random-addition strategies B, G and H. Strategies D, E and I lose nothing: D and I stay within a single service, and E is built from the curated pair list by construction.

### 3.2 Effect on the label distribution

| Risk label | Before | Removed | After |
|---|---:|---:|---:|
| Low | 226 | 0 | 226 |
| Medium | 483 | 5 | 478 |
| High | 631 | 90 | 541 |
| Critical | 505 | 86 | 419 |
| **Total** | **1845** | **181** | **1664** |

Removals fall almost entirely on Critical and High. This is the expected signature of the problem: implausible service mixes are broad and cross-service, so the point mapping scores them at the top of the scale. Pruning them both improves realism and reduces the over-representation of the Critical class.

### 3.3 Category by generation method

| Category | Strategy C: Removal | Strategy G: Plausable Cross Scope Combinations With Random Common Scope Addition | Strategy J: Bool Switching of Medium Risk Combinations | Strategy F: Randomly Generated Scope Combinations | Strategy B: Addition (student_gen) | Strategy A: Boolean Switching | Strategy H: Base Scope Combinations With Random Scope Addition | Strategy B: Addition (github manifest) | Student Created |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 0 | 0 | 0 | 10 | 0 | 0 | 1 | 0 | 0 |
| T2 | 3 | 0 | 0 | 13 | 3 | 1 | 1 | 0 | 1 |
| T3 | 0 | 19 | 2 | 21 | 15 | 0 | 5 | 5 | 0 |
| T4 | 3 | 4 | 1 | 15 | 8 | 1 | 3 | 6 | 1 |
| T5 | 4 | 6 | 0 | 16 | 4 | 0 | 8 | 0 | 0 |
| T6 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| **All** | **10** | **29** | **3** | **76** | **30** | **2** | **18** | **11** | **2** |

---

## 4. Removals

Scope URLs are abbreviated: the `https://www.googleapis.com/auth/` prefix is dropped. The pairing column lists only pairings that count — Fitness pairings are excluded per §2.4, so a row here may contain a Fitness scope without it appearing in the column.

### T1 — Multi-domain sprawl with no coherent application archetype

**11 rows removed.**

These combinations break three or more service pairings at once. No single application archetype explains them: they are the product of uniform random sampling over the scope catalog rather than of any development pattern. They are the clearest false-positive risk in the dataset, because the label pipeline scores them Critical on breadth alone while nothing resembling them would ever reach a consent screen.

#### Strategy F: Randomly Generated Scope Combinations (10 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0872 | AdSense, Calendar, Cloud Storage, Contacts, Tasks | AdSense + Calendar; AdSense + Contacts; AdSense + Tasks; Calendar + Cloud Storage; Cloud Storage + Tasks | Critical | calendar.events, adsense.readonly, contacts.readonly, tasks, devstorage.read_only |
| SC-0948 | Analytics, BigQuery, Calendar, Contacts | Analytics + Calendar; Analytics + Contacts; BigQuery + Calendar | High | analytics.readonly, calendar.readonly, bigquery.insertdata, user.addresses.read |
| SC-0949 | Analytics, BigQuery, Firebase, Fitness, Tasks | Analytics + Tasks; BigQuery + Tasks; Firebase + Tasks | Critical | firebase, analytics.manage.users, bigquery.insertdata, tasks.readonly, fitness.location.read |
| SC-0957 | Analytics, Fitness, Forms, Keep | Analytics + Forms; Analytics + Keep; Forms + Keep | Critical | analytics, keep, fitness.blood_glucose.read, forms.body.readonly |
| SC-0967 | Admin, Blogger, Cloud, Compute, Docs | Admin + Blogger; Blogger + Cloud; Blogger + Compute | Critical | cloud-platform.read-only, documents.readonly, admin.directory.user, blogger.readonly, compute.readonly |
| SC-0979 | AdSense, BigQuery, Chat, Drive, Firebase | AdSense + Chat; BigQuery + Chat; Chat + Firebase | High | bigquery.insertdata, firebase.messaging, drive.activity.readonly, adsense, chat.messages.readonly |
| SC-0981 | Admin, Analytics, Classroom, Gmail, YouTube | Admin + Analytics; Admin + YouTube; Analytics + Classroom | Critical | classroom.courses, youtube.upload, admin.directory.rolemanagement, gmail.modify, analytics |
| SC-0983 | Analytics, Chat, Cloud, Contacts, Gmail | Analytics + Chat; Analytics + Contacts; Chat + Cloud | Critical | analytics.edit, cloud-platform, gmail.settings.sharing, user.gender.read, chat.memberships |
| SC-0991 | Blogger, Calendar, Firebase, Fitness | Blogger + Calendar; Blogger + Firebase; Calendar + Firebase | High | fitness.activity.read, firebase.messaging, calendar.freebusy, blogger, firebase |
| SC-0995 | Analytics, Calendar, Compute, Gmail, Photos | Analytics + Calendar; Analytics + Photos; Calendar + Compute; Calendar + Photos | Critical | photoslibrary, calendar.acls, compute, analytics, gmail.addons.current.message.metadata |

#### Strategy H: Base Scope Combinations With Random Scope Addition (1 row)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-1244 | Calendar, Cloud Storage, Contacts, Drive, Gmail, Photos, YouTube | Calendar + Cloud Storage; Calendar + Photos; Contacts + YouTube | Critical | gmail.modify, drive, calendar, contacts, youtube, photoslibrary, devstorage.read_only |

### T2 — Domain administration combined with a consumer or marketing service

**22 rows removed.**

Workspace administration scopes are granted to domain-management tooling, which operates over the Workspace suite itself. The curated list accordingly admits Admin alongside Gmail, Drive, Contacts, Sheets, Apps Script, Classroom and the GCP services, and this analysis further admits Calendar, Chat, Forms, Tasks, Docs, Slides and Groups as suite-internal administration. What remains below pairs domain administration with consumer or marketing products that a Workspace administrator does not administer at all — Google Photos, YouTube, Blogger, AdSense and Analytics are outside the Workspace tenancy boundary.

#### Strategy C: Removal (3 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0509 | Admin, Analytics, Drive, Identity, Sheets | Admin + Analytics | Critical | openid, profile, admin.reports.audit.readonly, analytics.readonly, spreadsheets, drive.file |
| SC-0510 | Admin, Analytics, Drive, Identity, Sheets | Admin + Analytics | Critical | profile, email, admin.reports.audit.readonly, analytics.readonly, spreadsheets, drive.file |
| SC-0511 | Admin, Analytics, Drive, Identity, Sheets | Admin + Analytics | Critical | openid, email, admin.reports.audit.readonly, analytics.readonly, spreadsheets, drive.file |

#### Strategy F: Randomly Generated Scope Combinations (13 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0856 | Admin, Analytics, YouTube | Admin + Analytics; Admin + YouTube | Critical | admin.directory.user, youtube, analytics |
| SC-0861 | Admin, Analytics, Classroom | Admin + Analytics; Analytics + Classroom | Critical | classroom.courses.readonly, admin.directory.user.security, analytics.readonly |
| SC-0865 | Admin, Analytics, Drive, Forms | Admin + Analytics; Analytics + Forms | Critical | drive.file, admin.directory.user.readonly, admin.directory.user, analytics.manage.users, forms.body.readonly |
| SC-0878 | AdSense, Admin, Contacts | AdSense + Admin; AdSense + Contacts | Critical | adsense.readonly, admin.datatransfer, user.gender.read |
| SC-0886 | Admin, Analytics, Tasks | Admin + Analytics; Analytics + Tasks | Critical | admin.directory.group, tasks, analytics |
| SC-0916 | Admin, Fitness, YouTube | Admin + YouTube | Critical | fitness.blood_pressure.read, admin.datatransfer, fitness.sleep.read, admin.reports.audit.readonly, youtubepartner |
| SC-0931 | Admin, Cloud, Drive, Identity, Photos | Admin + Photos | Critical | profile, drive.file, cloud-platform.read-only, admin.datatransfer, photoslibrary |
| SC-0935 | Admin, Photos | Admin + Photos | Critical | admin.directory.group, photoslibrary.appendonly, admin.reports.audit.readonly |
| SC-0951 | Admin, Classroom, Fitness, Gmail, Photos | Admin + Photos; Classroom + Photos | Critical | admin.directory.user, photoslibrary.appendonly, gmail.labels, classroom.courses, fitness.sleep.read |
| SC-0955 | Admin, Docs, YouTube | Admin + YouTube | Critical | youtubepartner, documents, admin.reports.audit.readonly |
| SC-0970 | Admin, Blogger, Gmail | Admin + Blogger | Critical | https://mail.google.com/, admin.datatransfer, blogger.readonly |
| SC-0975 | Admin, Analytics, Calendar, Fitness | Admin + Analytics; Analytics + Calendar | Critical | calendar.calendars.readonly, analytics.manage.users, fitness.activity.write, admin.reports.audit.readonly |
| SC-0997 | Admin, Drive, Fitness, Photos | Admin + Photos | Critical | admin.directory.user.security, drive.readonly, photoslibrary, admin.directory.user, fitness.heart_rate.read |

#### Strategy B: Addition (student_gen) (3 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0356 | Admin, Analytics, Drive, Gmail, Identity, Sheets | Admin + Analytics | Critical | openid, profile, email, admin.reports.audit.readonly, analytics.readonly, spreadsheets, drive.file, gmail.send |
| SC-0357 | Admin, Analytics, Drive, Fitness, Identity, Sheets | Admin + Analytics | Critical | openid, profile, email, admin.reports.audit.readonly, analytics.readonly, spreadsheets, drive.file, fitness.activity.read |
| SC-0358 | Admin, Analytics, Calendar, Drive, Identity, Sheets | Admin + Analytics; Analytics + Calendar | Critical | openid, profile, email, admin.reports.audit.readonly, analytics.readonly, spreadsheets, drive.file, calendar.events.readonly |

#### Strategy A: Boolean Switching (1 row)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0119 | Admin, Analytics, Drive, Identity, Sheets | Admin + Analytics | Critical | openid, profile, email, admin.reports.audit.readonly, analytics.readonly, spreadsheets, drive.file |

#### Strategy H: Base Scope Combinations With Random Scope Addition (1 row)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-1223 | Admin, Chat, Gmail, Identity, Photos | Admin + Photos | Critical | openid, profile, email, photoslibrary.appendonly, chat.messages.readonly, gmail.addons.current.message.readonly, admin.directory.user |

#### Student Created (1 row)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0017 | Admin, Analytics, Drive, Identity, Sheets | Admin + Analytics | Critical | openid, profile, email, admin.reports.audit.readonly, analytics.readonly, spreadsheets, drive.file |

### T3 — Cloud / developer infrastructure combined with personal communication or PIM data

**67 rows removed.**

Cloud Platform, Compute, BigQuery, Cloud Storage and Firebase scopes are requested by developer and data tooling. Their legitimate consumer-side counterparts are document and file services (Drive, Docs, Sheets), which appear in export, backup and pipeline archetypes, plus Gmail and Contacts for the notification and CRM-sync patterns already in the curated list. The combinations below instead pair infrastructure management with personal calendars, notes, task lists or chat messages. There is no deployment, analytics or backup workflow in which a service account manager also needs the operator's personal to-do list.

#### Strategy G: Plausable Cross Scope Combinations With Random Common Scope Addition (19 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-1022 | Calendar, Cloud, Gmail | Calendar + Cloud | Critical | gmail.metadata, gmail.labels, cloud-platform, calendar.events.readonly |
| SC-1036 | Calendar, Contacts, Firebase | Calendar + Firebase | High | contacts.readonly, firebase.messaging, calendar.events.readonly |
| SC-1078 | Calendar, Cloud, Drive | Calendar + Cloud | Critical | drive.metadata, cloud-platform, calendar.events.readonly |
| SC-1079 | BigQuery, Drive, Tasks | BigQuery + Tasks | High | drive.appdata, drive.activity.readonly, bigquery.insertdata, tasks |
| SC-1080 | Compute, Drive, Tasks | Compute + Tasks | High | drive.activity.readonly, compute, tasks |
| SC-1087 | Firebase, Photos, Tasks | Firebase + Tasks | High | photoslibrary.readonly, photoslibrary.appendonly, firebase.readonly, firebase.messaging, tasks |
| SC-1102 | BigQuery, Docs, Tasks | BigQuery + Tasks | High | documents, bigquery, tasks |
| SC-1113 | Calendar, Cloud, Sheets | Calendar + Cloud | Critical | spreadsheets.readonly, spreadsheets, cloud-platform, cloud-platform.read-only, calendar.events.readonly |
| SC-1114 | BigQuery, Sheets, Tasks | BigQuery + Tasks | High | spreadsheets.readonly, bigquery.insertdata, bigquery, tasks |
| SC-1115 | Calendar, Compute, Sheets | Calendar + Compute | High | spreadsheets, spreadsheets.readonly, compute.readonly, compute, calendar.events.readonly |
| SC-1126 | Apps Script, Cloud, Tasks | Cloud + Tasks | High | script.deployments, script.projects, cloud-platform.read-only, tasks |
| SC-1128 | Apps Script, Chat, Compute | Chat + Compute | High | script.deployments, script.projects.readonly, compute.readonly, compute, chat.messages |
| SC-1133 | Calendar, Firebase, YouTube | Calendar + Firebase | High | firebase.readonly, youtube.force-ssl, youtube.readonly, calendar.events.readonly |
| SC-1135 | Calendar, Cloud, Firebase | Calendar + Cloud; Calendar + Firebase | High | firebase, firebase.readonly, cloud-platform, calendar.events.readonly |
| SC-1137 | Calendar, Compute, Firebase | Calendar + Compute; Calendar + Firebase | High | firebase.readonly, firebase.messaging, compute.readonly, compute, calendar.events.readonly |
| SC-1138 | AdSense, Firebase, Tasks | AdSense + Tasks; Firebase + Tasks | High | firebase.messaging, adsense, adsense.readonly, tasks |
| SC-1141 | Chat, Firebase, Identity | Chat + Firebase | High | firebase.readonly, firebase.messaging, email, userinfo.profile, chat.messages |
| SC-1162 | Analytics, Calendar, Cloud | Analytics + Calendar; Calendar + Cloud | Critical | cloud-platform, cloud-platform.read-only, analytics.manage.users, analytics.edit, calendar.events.readonly |
| SC-1169 | Chat, Cloud Storage, Compute | Chat + Cloud Storage; Chat + Compute | High | compute, compute.readonly, devstorage.full_control, chat.messages |

#### Strategy J: Bool Switching of Medium Risk Combinations (2 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-1139 | Analytics, Firebase, Tasks | Analytics + Tasks; Firebase + Tasks | High | firebase, analytics, tasks |
| SC-1219 | Analytics, Calendar, Firebase, Identity | Analytics + Calendar; Calendar + Firebase | High | openid, profile, email, firebase.readonly, analytics.readonly, calendar.events.owned.readonly |

#### Strategy F: Randomly Generated Scope Combinations (21 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0848 | Calendar, Cloud Storage, Drive, Gmail | Calendar + Cloud Storage | Critical | calendar.acls.readonly, drive.activity, devstorage.read_only, gmail.metadata, gmail.labels |
| SC-0851 | Calendar, Cloud Storage, Identity, Photos, YouTube | Calendar + Cloud Storage; Calendar + Photos | High | devstorage.read_only, photoslibrary.readonly.appcreateddata, youtube, calendar.readonly, email |
| SC-0862 | Calendar, Cloud Storage, Forms, Tasks | Calendar + Cloud Storage; Cloud Storage + Tasks | High | calendar.events.owned.readonly, forms.body, tasks, devstorage.read_write |
| SC-0877 | Calendar, Firebase, Identity, Slides, YouTube | Calendar + Firebase | High | presentations, youtube, firebase.readonly, profile, calendar.events.freebusy |
| SC-0879 | BigQuery, Chat, Cloud Storage | BigQuery + Chat; Chat + Cloud Storage | High | bigquery, chat.spaces, devstorage.read_only |
| SC-0883 | Calendar, Compute, Drive | Calendar + Compute | High | drive.photos.readonly, compute.readonly, calendar.acls |
| SC-0887 | Calendar, Contacts, Firebase, YouTube | Calendar + Firebase; Contacts + YouTube | Critical | firebase.readonly, calendar.readonly, user.gender.read, youtubepartner |
| SC-0896 | Calendar, Compute, Fitness, Gmail | Calendar + Compute | Critical | calendar.settings.readonly, compute, fitness.activity.write, gmail.addons.current.message.action |
| SC-0905 | Calendar, Cloud, Contacts, Slides | Calendar + Cloud | Critical | calendar.readonly, presentations, contacts, user.addresses.read, cloud-platform |
| SC-0912 | BigQuery, Calendar, Chat | BigQuery + Calendar; BigQuery + Chat | High | calendar.app.created, bigquery.insertdata, chat.messages |
| SC-0924 | Calendar, Cloud Storage, Contacts, Docs, Gmail | Calendar + Cloud Storage | Critical | gmail.addons.current.action.compose, calendar.app.created, devstorage.read_only, documents, user.addresses.read |
| SC-0928 | Compute, Drive, Firebase, Keep, Slides | Compute + Keep; Firebase + Keep | High | keep.readonly, firebase.readonly, presentations.readonly, compute, drive.photos.readonly |
| SC-0934 | BigQuery, Docs, Firebase, Keep | BigQuery + Keep; Firebase + Keep | High | documents, firebase.readonly, keep, bigquery.insertdata |
| SC-0946 | Apps Script, Chat, Cloud Storage, Drive, Gmail | Chat + Cloud Storage | Critical | gmail.readonly, chat.messages, devstorage.read_write, script.projects, drive.metadata |
| SC-0947 | Calendar, Cloud Storage, Firebase | Calendar + Cloud Storage; Calendar + Firebase | Medium | devstorage.full_control, firebase.messaging, calendar.app.created |
| SC-0956 | AdSense, Apps Script, Chat, Cloud Storage | AdSense + Chat; Chat + Cloud Storage | High | script.projects, adsense.readonly, chat.messages, devstorage.read_only |
| SC-0959 | Firebase, Identity, Keep | Firebase + Keep | High | email, firebase, keep.readonly |
| SC-0968 | Calendar, Cloud Storage, Drive, Fitness, Identity | Calendar + Cloud Storage | High | devstorage.read_write, fitness.blood_glucose.read, drive.appdata, calendar.acls, openid |
| SC-0984 | Calendar, Compute, Gmail, Identity, Tasks | Calendar + Compute; Compute + Tasks | High | compute.readonly, gmail.settings.sharing, userinfo.profile, tasks.readonly, calendar.events.freebusy |
| SC-0985 | Calendar, Firebase, Gmail, Slides | Calendar + Firebase | Critical | firebase.readonly, calendar.calendars.readonly, gmail.labels, presentations.readonly |
| SC-0999 | Calendar, Compute, Contacts, Fitness | Calendar + Compute | Critical | calendar.acls, compute.readonly, contacts.readonly, fitness.activity.read |

#### Strategy B: Addition (student_gen) (15 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0316 | Cloud Storage, Drive, Identity, Tasks | Cloud Storage + Tasks | Critical | openid, profile, email, devstorage.read_write, drive.file, tasks |
| SC-0326 | Compute, Firebase, Identity, Tasks | Compute + Tasks; Firebase + Tasks | High | openid, profile, email, firebase, compute, tasks |
| SC-0328 | Calendar, Compute, Firebase, Identity | Calendar + Compute; Calendar + Firebase | High | openid, profile, email, firebase, compute, calendar.events.readonly |
| SC-0346 | BigQuery, Chat, Cloud Storage | BigQuery + Chat; Chat + Cloud Storage | High | bigquery, devstorage.read_write, chat.messages |
| SC-0347 | Apps Script, Calendar, Firebase, Identity, Sheets | Calendar + Firebase | Critical | openid, profile, email, firebase, spreadsheets, script.deployments, script.projects, calendar.events.readonly |
| SC-0348 | Apps Script, Firebase, Identity, Sheets, Tasks | Firebase + Tasks | Critical | openid, profile, email, firebase, spreadsheets, script.deployments, script.projects, tasks |
| SC-0349 | Apps Script, Chat, Firebase, Identity, Sheets | Chat + Firebase | Critical | openid, profile, email, firebase, spreadsheets, script.deployments, script.projects, chat.messages |
| SC-0381 | Chat, Firebase, Fitness, Identity | Chat + Firebase | Critical | openid, profile, email, firebase, fitness.blood_glucose.read, chat.messages |
| SC-0390 | BigQuery, Chat, Drive | BigQuery + Chat | High | bigquery.insertdata, drive.readonly, chat.messages |
| SC-0392 | BigQuery, Drive, Tasks | BigQuery + Tasks | High | bigquery.insertdata, drive.readonly, tasks |
| SC-0420 | BigQuery, Chat, Cloud Storage, Sheets | BigQuery + Chat; Chat + Cloud Storage | Critical | bigquery, devstorage.read_write, spreadsheets, chat.messages |
| SC-0432 | Calendar, Compute, Firebase, Identity, Sheets | Calendar + Compute; Calendar + Firebase | High | openid, profile, email, compute.readonly, firebase.readonly, spreadsheets, calendar.events.readonly |
| SC-0433 | Compute, Firebase, Identity, Sheets, Tasks | Compute + Tasks; Firebase + Tasks | High | openid, profile, email, compute.readonly, firebase.readonly, spreadsheets, tasks |
| SC-0434 | Chat, Compute, Firebase, Identity, Sheets | Chat + Compute; Chat + Firebase | High | openid, profile, email, compute.readonly, firebase.readonly, spreadsheets, chat.messages |
| SC-0436 | Analytics, Firebase, Identity, Tasks | Analytics + Tasks; Firebase + Tasks | High | openid, profile, email, firebase.readonly, analytics.readonly, tasks |

#### Strategy H: Base Scope Combinations With Random Scope Addition (5 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-1179 | Calendar, Cloud Storage, Drive, Identity | Calendar + Cloud Storage | High | openid, profile, email, devstorage.read_write, drive.file, calendar.acls.readonly |
| SC-1201 | Chat, Firebase, Fitness, Identity | Chat + Firebase | Critical | openid, profile, email, firebase, fitness.blood_glucose.read, chat.delete |
| SC-1218 | Chat, Compute, Firebase, Identity, Sheets | Chat + Compute; Chat + Firebase | Critical | openid, profile, email, compute.readonly, firebase.readonly, spreadsheets, chat.memberships |
| SC-1262 | Analytics, BigQuery, Chat | Analytics + Chat; BigQuery + Chat | High | analytics, bigquery, chat.spaces |
| SC-1269 | Calendar, Chat, Cloud Storage | Calendar + Cloud Storage; Chat + Cloud Storage | High | chat.messages, chat.spaces, calendar.events.readonly, devstorage.read_only |

#### Strategy B: Addition (github manifest) (5 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0256 | Analytics, BigQuery, Chat | Analytics + Chat; BigQuery + Chat | High | analytics, bigquery, chat.messages |
| SC-0257 | Analytics, BigQuery, Tasks | Analytics + Tasks; BigQuery + Tasks | Medium | analytics, bigquery, tasks |
| SC-0298 | Cloud, Compute, Tasks | Cloud + Tasks; Compute + Tasks | Critical | cloud-platform, compute, tasks |
| SC-0300 | BigQuery, Chat, Cloud Storage | BigQuery + Chat; Chat + Cloud Storage | High | devstorage.read_write, bigquery, chat.messages |
| SC-0302 | Calendar, Cloud, Compute | Calendar + Cloud; Calendar + Compute | Medium | cloud-platform.read-only, compute.readonly, calendar.events.readonly |

### T4 — Marketing and monetization combined with personal data services

**42 rows removed.**

Analytics and AdSense scopes belong to site owners and publishers, and read aggregate traffic and revenue data. The combinations below attach that reporting access to an individual's contacts, calendar, notes, task list, photos or chat history. Audience measurement does not require the identity graph of the person who installed the reporting tool.

#### Strategy C: Removal (3 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0493 | Analytics, Contacts, Identity | Analytics + Contacts | High | openid, profile, userinfo.profile, analytics, user.addresses.read |
| SC-0494 | Analytics, Contacts, Identity | Analytics + Contacts | High | openid, email, userinfo.profile, analytics, user.addresses.read |
| SC-0496 | Analytics, Contacts, Identity | Analytics + Contacts | High | profile, email, userinfo.profile, analytics, user.addresses.read |

#### Strategy G: Plausable Cross Scope Combinations With Random Common Scope Addition (4 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-1130 | AdSense, Apps Script, Tasks | AdSense + Tasks | High | script.deployments, adsense.readonly, tasks |
| SC-1166 | AdSense, BigQuery, Contacts | AdSense + Contacts | High | bigquery, bigquery.insertdata, adsense.readonly, contacts.readonly |
| SC-1167 | Analytics, BigQuery, Contacts | Analytics + Contacts | High | bigquery.insertdata, analytics.manage.users, contacts.readonly |
| SC-1172 | AdSense, Analytics, Calendar | AdSense + Calendar; Analytics + Calendar | High | adsense, analytics.edit, calendar.events.readonly |

#### Strategy J: Bool Switching of Medium Risk Combinations (1 row)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0908 | Analytics, Chat, Identity | Analytics + Chat | High | userinfo.email, analytics.readonly, chat.messages.readonly |

#### Strategy F: Randomly Generated Scope Combinations (15 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0853 | Analytics, Calendar, Gmail, Tasks | Analytics + Calendar; Analytics + Tasks | Critical | tasks, gmail.send, analytics.readonly, calendar.calendars.readonly |
| SC-0858 | Analytics, Contacts, Drive, Forms | Analytics + Contacts; Analytics + Forms | Critical | drive.metadata.readonly, contacts.other.readonly, forms, contacts, analytics.edit |
| SC-0867 | Analytics, Gmail, Tasks | Analytics + Tasks | Critical | analytics, https://mail.google.com/, tasks |
| SC-0894 | Analytics, Calendar, Drive | Analytics + Calendar | High | analytics.readonly, calendar.acls, drive.metadata.readonly |
| SC-0919 | Analytics, Classroom, Compute, Fitness, Identity | Analytics + Classroom | High | fitness.location.read, analytics.manage.users, compute.readonly, profile, classroom.coursework.students |
| SC-0925 | Analytics, Calendar, Forms | Analytics + Calendar; Analytics + Forms | High | forms.body, calendar.calendars.readonly, analytics |
| SC-0927 | AdSense, Blogger, Forms | AdSense + Forms; Blogger + Forms | High | adsense.readonly, blogger.readonly, forms.currentonly |
| SC-0937 | Analytics, Contacts, Gmail | Analytics + Contacts | High | analytics.edit, user.birthday.read, gmail.settings.basic |
| SC-0938 | Analytics, Fitness, Identity, Photos | Analytics + Photos | High | fitness.sleep.read, profile, analytics, photoslibrary.appendonly |
| SC-0939 | AdSense, Cloud Storage, Drive, Forms | AdSense + Forms | Critical | devstorage.full_control, forms.body.readonly, drive.readonly, adsense |
| SC-0942 | AdSense, Calendar, Identity | AdSense + Calendar | Medium | adsense.readonly, calendar.calendarlist.readonly, email |
| SC-0978 | AdSense, Compute, Contacts, Gmail, YouTube | AdSense + Contacts; Contacts + YouTube | Critical | gmail.readonly, directory.readonly, adsense, compute.readonly, youtube |
| SC-0988 | AdSense, Analytics, Firebase, Forms | AdSense + Forms; Analytics + Forms | High | firebase, adsense, forms, analytics |
| SC-0992 | Analytics, Apps Script, Contacts, Fitness | Analytics + Contacts | Critical | script.deployments, analytics, fitness.location.read, user.gender.read |
| SC-0996 | AdSense, Calendar, Drive, Tasks | AdSense + Calendar; AdSense + Tasks | High | calendar.readonly, drive.photos.readonly, adsense, tasks |

#### Strategy B: Addition (student_gen) (8 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0338 | Analytics, Calendar, Contacts, Identity | Analytics + Calendar; Analytics + Contacts | High | openid, profile, email, userinfo.profile, analytics, user.addresses.read, calendar.events.readonly |
| SC-0339 | Analytics, Contacts, Gmail, Identity | Analytics + Contacts | Critical | openid, profile, email, userinfo.profile, analytics, user.addresses.read, gmail.send |
| SC-0340 | Analytics, Contacts, Fitness, Identity | Analytics + Contacts | High | openid, profile, email, userinfo.profile, analytics, user.addresses.read, fitness.activity.read |
| SC-0365 | Analytics, Apps Script, Blogger, Calendar, Identity | Analytics + Calendar; Blogger + Calendar | High | openid, profile, email, blogger, analytics, script.projects, calendar.events.readonly |
| SC-0366 | Analytics, Apps Script, Blogger, Contacts, Identity | Analytics + Contacts; Blogger + Contacts | Critical | openid, profile, email, blogger, analytics, script.projects, contacts.readonly |
| SC-0399 | Analytics, Chat, Identity, Sheets | Analytics + Chat | Critical | openid, profile, email, analytics.readonly, spreadsheets, chat.messages |
| SC-0400 | Analytics, Calendar, Identity, Sheets | Analytics + Calendar | Critical | openid, profile, email, analytics.readonly, spreadsheets, calendar.events.readonly |
| SC-0448 | AdSense, Analytics, Identity, Tasks | AdSense + Tasks; Analytics + Tasks | High | openid, profile, email, adsense.readonly, analytics.readonly, tasks |

#### Strategy A: Boolean Switching (1 row)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0114 | Analytics, Contacts, Identity | Analytics + Contacts | Critical | openid, profile, email, userinfo.profile, analytics, user.addresses.read |

#### Strategy H: Base Scope Combinations With Random Scope Addition (3 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-1187 | Analytics, Contacts, Identity, Photos | Analytics + Contacts; Analytics + Photos | High | openid, profile, email, userinfo.profile, analytics, user.addresses.read, photoslibrary.readonly.appcreateddata |
| SC-1195 | Analytics, Apps Script, Blogger, Chat, Identity | Analytics + Chat; Blogger + Chat | Critical | openid, profile, email, blogger, analytics, script.projects, chat.memberships |
| SC-1261 | Analytics, Calendar, Sheets | Analytics + Calendar | High | analytics.readonly, spreadsheets, calendar |

#### Strategy B: Addition (github manifest) (6 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0252 | Analytics, Sheets, Tasks | Analytics + Tasks | High | analytics.readonly, spreadsheets, tasks |
| SC-0253 | Analytics, Contacts, Sheets | Analytics + Contacts | High | analytics.readonly, spreadsheets, contacts.readonly |
| SC-0254 | Analytics, Calendar, Sheets | Analytics + Calendar | High | analytics.readonly, spreadsheets, calendar.events.readonly |
| SC-0255 | Analytics, BigQuery, Contacts | Analytics + Contacts | High | analytics, bigquery, contacts.readonly |
| SC-0264 | Analytics, Tasks, YouTube | Analytics + Tasks | High | youtube, analytics.readonly, tasks |
| SC-0266 | Analytics, Contacts, YouTube | Analytics + Contacts; Contacts + YouTube | Critical | youtube, analytics.readonly, contacts.readonly |

#### Student Created (1 row)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0011 | Analytics, Contacts, Identity | Analytics + Contacts | High | openid, profile, email, userinfo.profile, analytics, user.addresses.read |

### T5 — Consumer media combined with an unrelated productivity or enterprise service

**38 rows removed.**

YouTube, Photos and Blogger are consumer publishing and media products. The curated list already pairs them with the services a creator workflow touches — Drive, Docs, Sheets, Slides, Gmail. What remains pairs a media product with an unrelated productivity, education or enterprise service, where no upload, publishing or library-management workflow explains the second service.

#### Strategy C: Removal (4 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0630 | Contacts, Drive, Gmail, Photos, YouTube | Contacts + YouTube | Critical | gmail.modify, drive, contacts, youtube, photoslibrary |
| SC-0631 | Calendar, Contacts, Drive, Photos, YouTube | Calendar + Photos; Contacts + YouTube | Critical | drive, calendar, contacts, youtube, photoslibrary |
| SC-0632 | Calendar, Contacts, Drive, Gmail, YouTube | Contacts + YouTube | Critical | gmail.modify, drive, calendar, contacts, youtube |
| SC-0633 | Calendar, Drive, Gmail, Photos, YouTube | Calendar + Photos | Critical | gmail.modify, drive, calendar, youtube, photoslibrary |

#### Strategy G: Plausable Cross Scope Combinations With Random Common Scope Addition (6 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-1025 | Blogger, Calendar, Gmail | Blogger + Calendar | Critical | gmail.addons.current.message.readonly, blogger, blogger.readonly, calendar.events.readonly |
| SC-1081 | Blogger, Contacts, Drive | Blogger + Contacts | Critical | drive.metadata.readonly, blogger.readonly, blogger, contacts.readonly |
| SC-1089 | Calendar, Photos, Slides | Calendar + Photos | High | photoslibrary.readonly.appcreateddata, photoslibrary, presentations.readonly, calendar.events.readonly |
| SC-1122 | Apps Script, Contacts, YouTube | Contacts + YouTube | Critical | script.projects, script.deployments, youtube.force-ssl, contacts.readonly |
| SC-1129 | Apps Script, Blogger, Chat | Blogger + Chat | High | script.projects, blogger.readonly, blogger, chat.messages |
| SC-1144 | Cloud, Contacts, YouTube | Contacts + YouTube | Critical | youtube.force-ssl, cloud-platform, cloud-platform.read-only, contacts.readonly |

#### Strategy F: Randomly Generated Scope Combinations (16 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0850 | Blogger, Cloud Storage, Docs, Gmail, YouTube | Blogger + Cloud Storage | Critical | devstorage.full_control, documents, blogger, youtube, gmail.addons.current.action.compose |
| SC-0854 | Chat, Contacts, YouTube | Contacts + YouTube | High | youtubepartner, chat.memberships, user.organization.read |
| SC-0866 | Calendar, Photos, Tasks, YouTube | Calendar + Photos | High | calendar.calendarlist.readonly, tasks.readonly, photoslibrary.readonly.appcreateddata, calendar.calendarlist, youtubepartner |
| SC-0882 | Cloud Storage, Contacts, YouTube | Contacts + YouTube | High | devstorage.read_only, user.birthday.read, youtube |
| SC-0900 | Calendar, Gmail, Photos | Calendar + Photos | Critical | https://mail.google.com/, photoslibrary.readonly, calendar.events.freebusy |
| SC-0906 | Cloud, Forms, Photos | Forms + Photos | High | photoslibrary.readonly, cloud-platform, forms.body |
| SC-0911 | Calendar, Contacts, Forms, Gmail, Photos | Calendar + Photos; Forms + Photos | Critical | photoslibrary, gmail.labels, calendar.calendarlist.readonly, forms.currentonly, user.addresses.read |
| SC-0915 | Calendar, Drive, Fitness, Photos | Calendar + Photos | High | drive.metadata, photoslibrary, fitness.body.read, calendar.calendars.readonly |
| SC-0920 | Contacts, Drive, Photos, YouTube | Contacts + YouTube | High | contacts.other.readonly, drive.scripts, youtube.readonly, photoslibrary.readonly, drive.activity.readonly |
| SC-0950 | Blogger, Forms, YouTube | Blogger + Forms; Forms + YouTube | Medium | youtube, blogger.readonly, forms |
| SC-0952 | Chat, Forms, Identity, Photos | Forms + Photos | High | profile, chat.spaces, forms.currentonly, photoslibrary.readonly.appcreateddata |
| SC-0954 | AdSense, Blogger, Firebase, Slides | Blogger + Firebase | High | presentations.readonly, adsense.readonly, firebase.messaging, blogger |
| SC-0960 | Contacts, Sheets, YouTube | Contacts + YouTube | High | user.organization.read, youtubepartner, spreadsheets |
| SC-0964 | Contacts, Forms, Gmail, Photos | Forms + Photos | High | photoslibrary.readonly.appcreateddata, user.emails.read, gmail.settings.sharing, forms.body.readonly |
| SC-0980 | Calendar, Contacts, Fitness, Photos | Calendar + Photos | Critical | fitness.location.read, calendar.acls.readonly, contacts, photoslibrary |
| SC-0990 | Classroom, Gmail, Photos, Tasks | Classroom + Photos | Critical | photoslibrary.readonly.appcreateddata, classroom.profile.emails, tasks.readonly, https://mail.google.com/ |

#### Strategy B: Addition (student_gen) (4 rows)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0310 | Contacts, Drive, Identity, YouTube | Contacts + YouTube | Critical | openid, profile, email, youtube, drive.file, contacts.readonly |
| SC-0394 | Contacts, Drive, Identity, YouTube | Contacts + YouTube | Critical | openid, profile, email, drive.readonly, youtube.upload, contacts.readonly |
| SC-0405 | Blogger, Docs, Identity, Tasks | Blogger + Tasks | High | openid, profile, email, blogger, documents.readonly, tasks |
| SC-0406 | Blogger, Calendar, Docs, Identity | Blogger + Calendar | High | openid, profile, email, blogger, documents.readonly, calendar.events.readonly |

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

### T6 — Incoherent productivity / PIM pairing

**1 rows removed.**

Productivity and PIM services that are individually ordinary but have no shared workflow. These are residual: the pairing is not administrative, infrastructural, marketing or media, it is simply two personal-data services with no application that reads both.

#### Strategy F: Randomly Generated Scope Combinations (1 row)

| SC ID | Services | Implausible pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0847 | Calendar, Docs, Forms, Gmail, Keep | Forms + Keep | Critical | calendar.calendarlist, gmail.insert, keep.readonly, forms, documents.readonly |

---

## 5. Health and fitness combinations (disclosure, not a category)

71 rows pair a Google Fitness scope with a service outside the wellness archetype. Per §2.4 that pairing is not a removal ground and these rows are not a category. They are listed here so the decision is auditable and so the rule can be reversed if the project later decides health pairings should be filtered.

|  | Rows |
|---|---:|
| Health-bearing rows, kept (no other implausible pairing) | 53 |
| Health-bearing rows, removed on a non-health pairing (§5.2) | 18 |
| **Total health-bearing rows** | **71** |

| Generation method | Kept | Removed (non-health grounds) | Total |
|---|---:|---:|---:|
| Strategy F: Randomly Generated Scope Combinations | 19 | 14 | 33 |
| Strategy B: Addition (student_gen) | 16 | 3 | 19 |
| Strategy B: Addition (github manifest) | 6 | 0 | 6 |
| Strategy G: Plausable Cross Scope Combinations With Random Common Scope Addition | 4 | 0 | 4 |
| Strategy H: Base Scope Combinations With Random Scope Addition | 3 | 1 | 4 |
| Strategy C: Removal | 3 | 0 | 3 |
| Strategy A: Boolean Switching | 1 | 0 | 1 |
| Student Created | 1 | 0 | 1 |
| **All** | **53** | **18** | **71** |

### 5.1 Health-bearing rows retained

**53 rows.** These carry a Fitness pairing and nothing else the filter objects to, so they survive. Their risk labels are unchanged. The "Health pairing(s)" column records what the filter would have objected to had §2.4 not applied.

#### Strategy C: Removal (3 rows)

| SC ID | Services | Health pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0529 | Firebase, Fitness, Identity | Firebase + Fitness | High | openid, profile, firebase, fitness.blood_glucose.read |
| SC-0530 | Firebase, Fitness, Identity | Firebase + Fitness | High | profile, email, firebase, fitness.blood_glucose.read |
| SC-0532 | Firebase, Fitness, Identity | Firebase + Fitness | High | openid, email, firebase, fitness.blood_glucose.read |

#### Strategy G: Plausable Cross Scope Combinations With Random Common Scope Addition (4 rows)

| SC ID | Services | Health pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-1044 | Contacts, Fitness, Keep | Contacts + Fitness | High | keep.readonly, fitness.body.read, fitness.activity.read, contacts.readonly |
| SC-1063 | Drive, Fitness, Gmail | Fitness + Gmail | Critical | fitness.sleep.read, fitness.location.read, drive.file, gmail.send |
| SC-1064 | Contacts, Fitness, Photos | Contacts + Fitness | High | fitness.blood_pressure.read, fitness.blood_glucose.read, photoslibrary, photoslibrary.readonly, contacts.readonly |
| SC-1068 | Chat, Fitness, Identity | Chat + Fitness | High | fitness.blood_glucose.read, userinfo.profile, chat.messages |

#### Strategy F: Randomly Generated Scope Combinations (19 rows)

| SC ID | Services | Health pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0868 | Calendar, Classroom, Contacts, Fitness | Classroom + Fitness; Contacts + Fitness | High | calendar.app.created, fitness.activity.read, classroom.profile.emails, user.phonenumbers.read, calendar.readonly |
| SC-0869 | Firebase, Fitness, Gmail | Firebase + Fitness; Fitness + Gmail | Critical | https://mail.google.com/, fitness.location.read, firebase.messaging |
| SC-0870 | Chat, Fitness, Slides | Chat + Fitness | High | chat.memberships, fitness.blood_glucose.read, presentations.readonly |
| SC-0873 | Admin, Apps Script, Compute, Fitness, Identity | Admin + Fitness; Compute + Fitness | Critical | userinfo.email, fitness.blood_pressure.read, admin.directory.rolemanagement, script.projects.readonly, compute |
| SC-0891 | Cloud Storage, Drive, Fitness, Forms, Gmail | Cloud Storage + Fitness; Fitness + Gmail | Critical | forms.body, gmail.readonly, drive.readonly, devstorage.full_control, fitness.body.read |
| SC-0893 | Analytics, Fitness | Analytics + Fitness | Medium | fitness.activity.read, analytics.readonly, fitness.body.read |
| SC-0903 | Calendar, Chat, Fitness, Gmail | Chat + Fitness; Fitness + Gmail | Critical | calendar.events, gmail.readonly, fitness.blood_glucose.read, chat.delete |
| SC-0918 | Fitness, Gmail, Identity, YouTube | Fitness + Gmail; Fitness + YouTube | Critical | https://mail.google.com/, fitness.activity.write, youtube.upload, openid |
| SC-0921 | Calendar, Contacts, Docs, Fitness, Gmail | Contacts + Fitness; Fitness + Gmail | Critical | fitness.blood_pressure.read, documents.readonly, user.phonenumbers.read, calendar.events.readonly, gmail.insert |
| SC-0926 | Classroom, Cloud Storage, Compute, Fitness | Classroom + Fitness; Cloud Storage + Fitness; Compute + Fitness | High | fitness.heart_rate.read, compute.readonly, classroom.profile.emails, devstorage.read_write |
| SC-0933 | Admin, Chat, Fitness, Gmail, Groups | Admin + Fitness; Chat + Fitness; Fitness + Gmail; Fitness + Groups | Critical | admin.directory.user, groups, gmail.addons.current.action.compose, chat.spaces, fitness.activity.read |
| SC-0944 | Apps Script, Fitness, Gmail | Fitness + Gmail | High | gmail.insert, fitness.blood_pressure.read, script.deployments |
| SC-0945 | Calendar, Contacts, Drive, Fitness, Forms | Contacts + Fitness | High | user.phonenumbers.read, drive.photos.readonly, forms, calendar.acls.readonly, fitness.activity.write |
| SC-0958 | Calendar, Contacts, Fitness | Contacts + Fitness | High | user.organization.read, fitness.body.read, calendar.calendars |
| SC-0961 | Calendar, Fitness, Gmail | Fitness + Gmail | High | fitness.activity.write, gmail.addons.current.message.metadata, calendar.events |
| SC-0966 | Calendar, Drive, Fitness, Forms, Gmail | Fitness + Gmail | Critical | gmail.settings.sharing, calendar.freebusy, fitness.activity.write, drive.scripts, forms.body |
| SC-0974 | Contacts, Drive, Fitness | Contacts + Fitness | High | drive.appdata, contacts.readonly, fitness.blood_glucose.read |
| SC-0982 | Admin, Calendar, Fitness, Forms | Admin + Fitness | High | forms.body.readonly, fitness.location.read, calendar.calendarlist.readonly, admin.reports.audit.readonly |
| SC-0993 | Admin, Cloud, Fitness, Gmail, Sheets | Admin + Fitness; Cloud + Fitness; Fitness + Gmail | Critical | admin.directory.user.readonly, spreadsheets.readonly, cloud-platform, gmail.send, fitness.heart_rate.read |

#### Strategy B: Addition (student_gen) (16 rows)

| SC ID | Services | Health pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0305 | Contacts, Fitness, Identity, Sheets | Contacts + Fitness | Critical | openid, profile, email, fitness.activity.read, fitness.body.read, spreadsheets, contacts.readonly |
| SC-0306 | Fitness, Gmail, Identity, Sheets | Fitness + Gmail | Critical | openid, profile, email, fitness.activity.read, fitness.body.read, spreadsheets, gmail.send |
| SC-0309 | Drive, Fitness, Identity, YouTube | Fitness + YouTube | High | openid, profile, email, youtube, drive.file, fitness.activity.read |
| SC-0312 | Contacts, Fitness, Gmail, Identity | Contacts + Fitness; Fitness + Gmail | Critical | openid, profile, email, contacts.readonly, gmail.compose, fitness.activity.read |
| SC-0327 | Compute, Firebase, Fitness, Identity | Compute + Fitness; Firebase + Fitness | High | openid, profile, email, firebase, compute, fitness.activity.read |
| SC-0332 | Chat, Contacts, Fitness, Identity | Chat + Fitness; Contacts + Fitness | Critical | openid, profile, email, chat.messages, contacts.readonly, fitness.activity.read |
| SC-0345 | BigQuery, Cloud Storage, Fitness | BigQuery + Fitness; Cloud Storage + Fitness | High | bigquery, devstorage.read_write, fitness.activity.read |
| SC-0359 | Chat, Drive, Fitness, Identity | Chat + Fitness | Critical | openid, profile, email, chat.messages, drive.readonly, fitness.activity.read |
| SC-0382 | Firebase, Fitness, Gmail, Identity | Firebase + Fitness; Fitness + Gmail | Critical | openid, profile, email, firebase, fitness.blood_glucose.read, gmail.send |
| SC-0383 | Contacts, Firebase, Fitness, Identity | Contacts + Fitness; Firebase + Fitness | Critical | openid, profile, email, firebase, fitness.blood_glucose.read, contacts.readonly |
| SC-0418 | Calendar, Chat, Fitness, Identity | Chat + Fitness | High | openid, profile, email, calendar.events.owned, chat.messages.readonly, fitness.activity.read |
| SC-0422 | BigQuery, Cloud Storage, Fitness, Sheets | BigQuery + Fitness; Cloud Storage + Fitness | Critical | bigquery, devstorage.read_write, spreadsheets, fitness.activity.read |
| SC-0424 | Admin, Fitness, Gmail, Identity | Admin + Fitness; Fitness + Gmail | Critical | openid, profile, email, gmail.send, admin.datatransfer, fitness.activity.read |
| SC-0427 | Drive, Fitness, Gmail, Identity | Fitness + Gmail | Critical | openid, profile, email, drive.activity.readonly, gmail.send, fitness.activity.read |
| SC-0441 | Calendar, Classroom, Fitness, Gmail, Identity | Classroom + Fitness; Fitness + Gmail | Critical | openid, profile, email, gmail.send, classroom.profile.emails, calendar.events.readonly, fitness.activity.read |
| SC-0451 | Chat, Fitness, Gmail, Identity, Photos | Chat + Fitness; Fitness + Gmail | High | openid, profile, email, photoslibrary.appendonly, chat.messages.readonly, gmail.addons.current.message.readonly, fitness.activity.read |

#### Strategy A: Boolean Switching (1 row)

| SC ID | Services | Health pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0128 | Firebase, Fitness, Identity | Firebase + Fitness | High | openid, profile, email, firebase, fitness.blood_glucose.read |

#### Strategy H: Base Scope Combinations With Random Scope Addition (3 rows)

| SC ID | Services | Health pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-1212 | Chat, Fitness, Gmail, Identity | Chat + Fitness; Fitness + Gmail | Critical | openid, profile, email, gmail.addons.current.message.readonly, chat.messages, fitness.body.read |
| SC-1232 | Fitness, Gmail | Fitness + Gmail | High | gmail.modify, gmail.settings.basic, fitness.activity.read |
| SC-1235 | Admin, Fitness | Admin + Fitness | Critical | admin.directory.user, admin.directory.group, admin.directory.domain, admin.datatransfer, fitness.location.read |

#### Strategy B: Addition (github manifest) (6 rows)

| SC ID | Services | Health pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0213 | Calendar, Contacts, Fitness, Gmail | Contacts + Fitness; Fitness + Gmail | Critical | gmail.send, gmail.readonly, contacts.readonly, calendar.events, fitness.activity.read |
| SC-0218 | Calendar, Contacts, Drive, Fitness, Gmail | Contacts + Fitness; Fitness + Gmail | Critical | contacts, gmail.send, calendar.events, drive.file, fitness.activity.read |
| SC-0240 | Drive, Fitness, Gmail, Sheets | Fitness + Gmail | Critical | spreadsheets, gmail.send, drive.file, fitness.activity.read |
| SC-0247 | Apps Script, Drive, Fitness, Gmail, Sheets | Fitness + Gmail | Critical | script.projects, drive, spreadsheets, gmail.send, fitness.activity.read |
| SC-0299 | Cloud, Compute, Fitness | Cloud + Fitness; Compute + Fitness | Critical | cloud-platform, compute, fitness.activity.read |
| SC-0301 | BigQuery, Cloud Storage, Fitness | BigQuery + Fitness; Cloud Storage + Fitness | High | devstorage.read_write, bigquery, fitness.activity.read |

#### Student Created (1 row)

| SC ID | Services | Health pairing(s) | Risk label | Scopes |
|---|---|---|---|---|
| SC-0026 | Firebase, Fitness, Identity | Firebase + Fitness | High | openid, profile, email, firebase, fitness.blood_glucose.read |

### 5.2 Health-bearing rows removed on non-health grounds

**18 rows.** Each of these contains health data *and* breaks a pairing that has nothing to do with health, and is removed on the latter. This is the one place where the change described in §2.4 alters an outcome rather than only the bookkeeping: the previous report retained rows of this shape. Adding these ids back is sufficient to restore the old behaviour.

| SC ID | Generation method | Category | Non-health pairing(s) | Health pairing(s) | Risk label |
|---|---|---|---|---|---|
| SC-0340 | Strategy B: Addition (student_gen) | T4 | Analytics + Contacts | Analytics + Fitness; Contacts + Fitness | High |
| SC-0357 | Strategy B: Addition (student_gen) | T2 | Admin + Analytics | Admin + Fitness; Analytics + Fitness | Critical |
| SC-0381 | Strategy B: Addition (student_gen) | T3 | Chat + Firebase | Chat + Fitness; Firebase + Fitness | Critical |
| SC-0896 | Strategy F: Randomly Generated Scope Combinations | T3 | Calendar + Compute | Compute + Fitness; Fitness + Gmail | Critical |
| SC-0916 | Strategy F: Randomly Generated Scope Combinations | T2 | Admin + YouTube | Admin + Fitness; Fitness + YouTube | Critical |
| SC-0919 | Strategy F: Randomly Generated Scope Combinations | T4 | Analytics + Classroom | Analytics + Fitness; Classroom + Fitness; Compute + Fitness | High |
| SC-0938 | Strategy F: Randomly Generated Scope Combinations | T4 | Analytics + Photos | Analytics + Fitness | High |
| SC-0949 | Strategy F: Randomly Generated Scope Combinations | T1 | Analytics + Tasks; BigQuery + Tasks; Firebase + Tasks | Analytics + Fitness; BigQuery + Fitness; Firebase + Fitness | Critical |
| SC-0951 | Strategy F: Randomly Generated Scope Combinations | T2 | Admin + Photos; Classroom + Photos | Admin + Fitness; Classroom + Fitness; Fitness + Gmail | Critical |
| SC-0957 | Strategy F: Randomly Generated Scope Combinations | T1 | Analytics + Forms; Analytics + Keep; Forms + Keep | Analytics + Fitness | Critical |
| SC-0968 | Strategy F: Randomly Generated Scope Combinations | T3 | Calendar + Cloud Storage | Cloud Storage + Fitness | High |
| SC-0975 | Strategy F: Randomly Generated Scope Combinations | T2 | Admin + Analytics; Analytics + Calendar | Admin + Fitness; Analytics + Fitness | Critical |
| SC-0980 | Strategy F: Randomly Generated Scope Combinations | T5 | Calendar + Photos | Contacts + Fitness | Critical |
| SC-0991 | Strategy F: Randomly Generated Scope Combinations | T1 | Blogger + Calendar; Blogger + Firebase; Calendar + Firebase | Blogger + Fitness; Firebase + Fitness | High |
| SC-0992 | Strategy F: Randomly Generated Scope Combinations | T4 | Analytics + Contacts | Analytics + Fitness; Contacts + Fitness | Critical |
| SC-0997 | Strategy F: Randomly Generated Scope Combinations | T2 | Admin + Photos | Admin + Fitness | Critical |
| SC-0999 | Strategy F: Randomly Generated Scope Combinations | T3 | Calendar + Compute | Compute + Fitness; Contacts + Fitness | Critical |
| SC-1201 | Strategy H: Base Scope Combinations With Random Scope Addition | T3 | Chat + Firebase | Chat + Fitness; Firebase + Fitness | Critical |

---

## 6. Removal list

All 181 removed ids, in dataset order.

```
SC-0011, SC-0017, SC-0114, SC-0119, SC-0252, SC-0253, SC-0254, SC-0255, SC-0256, SC-0257
SC-0264, SC-0266, SC-0298, SC-0300, SC-0302, SC-0310, SC-0316, SC-0326, SC-0328, SC-0338
SC-0339, SC-0340, SC-0346, SC-0347, SC-0348, SC-0349, SC-0356, SC-0357, SC-0358, SC-0365
SC-0366, SC-0381, SC-0390, SC-0392, SC-0394, SC-0399, SC-0400, SC-0405, SC-0406, SC-0420
SC-0432, SC-0433, SC-0434, SC-0436, SC-0448, SC-0493, SC-0494, SC-0496, SC-0509, SC-0510
SC-0511, SC-0630, SC-0631, SC-0632, SC-0633, SC-0847, SC-0848, SC-0850, SC-0851, SC-0853
SC-0854, SC-0856, SC-0858, SC-0861, SC-0862, SC-0865, SC-0866, SC-0867, SC-0872, SC-0877
SC-0878, SC-0879, SC-0882, SC-0883, SC-0886, SC-0887, SC-0894, SC-0896, SC-0900, SC-0905
SC-0906, SC-0908, SC-0911, SC-0912, SC-0915, SC-0916, SC-0919, SC-0920, SC-0924, SC-0925
SC-0927, SC-0928, SC-0931, SC-0934, SC-0935, SC-0937, SC-0938, SC-0939, SC-0942, SC-0946
SC-0947, SC-0948, SC-0949, SC-0950, SC-0951, SC-0952, SC-0954, SC-0955, SC-0956, SC-0957
SC-0959, SC-0960, SC-0964, SC-0967, SC-0968, SC-0970, SC-0975, SC-0978, SC-0979, SC-0980
SC-0981, SC-0983, SC-0984, SC-0985, SC-0988, SC-0990, SC-0991, SC-0992, SC-0995, SC-0996
SC-0997, SC-0999, SC-1022, SC-1025, SC-1036, SC-1078, SC-1079, SC-1080, SC-1081, SC-1087
SC-1089, SC-1102, SC-1113, SC-1114, SC-1115, SC-1122, SC-1126, SC-1128, SC-1129, SC-1130
SC-1133, SC-1135, SC-1137, SC-1138, SC-1139, SC-1141, SC-1144, SC-1162, SC-1166, SC-1167
SC-1169, SC-1172, SC-1177, SC-1179, SC-1185, SC-1186, SC-1187, SC-1195, SC-1200, SC-1201
SC-1205, SC-1218, SC-1219, SC-1223, SC-1244, SC-1250, SC-1255, SC-1261, SC-1262, SC-1268
SC-1269
```

### 6.1 Same list, grouped by category

**T1** (11): SC-0872, SC-0948, SC-0949, SC-0957, SC-0967, SC-0979, SC-0981, SC-0983, SC-0991, SC-0995, SC-1244

**T2** (22): SC-0017, SC-0119, SC-0356, SC-0357, SC-0358, SC-0509, SC-0510, SC-0511, SC-0856, SC-0861, SC-0865, SC-0878, SC-0886, SC-0916, SC-0931, SC-0935, SC-0951, SC-0955, SC-0970, SC-0975, SC-0997, SC-1223

**T3** (67): SC-0256, SC-0257, SC-0298, SC-0300, SC-0302, SC-0316, SC-0326, SC-0328, SC-0346, SC-0347, SC-0348, SC-0349, SC-0381, SC-0390, SC-0392, SC-0420, SC-0432, SC-0433, SC-0434, SC-0436, SC-0848, SC-0851, SC-0862, SC-0877, SC-0879, SC-0883, SC-0887, SC-0896, SC-0905, SC-0912, SC-0924, SC-0928, SC-0934, SC-0946, SC-0947, SC-0956, SC-0959, SC-0968, SC-0984, SC-0985, SC-0999, SC-1022, SC-1036, SC-1078, SC-1079, SC-1080, SC-1087, SC-1102, SC-1113, SC-1114, SC-1115, SC-1126, SC-1128, SC-1133, SC-1135, SC-1137, SC-1138, SC-1139, SC-1141, SC-1162, SC-1169, SC-1179, SC-1201, SC-1218, SC-1219, SC-1262, SC-1269

**T4** (42): SC-0011, SC-0114, SC-0252, SC-0253, SC-0254, SC-0255, SC-0264, SC-0266, SC-0338, SC-0339, SC-0340, SC-0365, SC-0366, SC-0399, SC-0400, SC-0448, SC-0493, SC-0494, SC-0496, SC-0853, SC-0858, SC-0867, SC-0894, SC-0908, SC-0919, SC-0925, SC-0927, SC-0937, SC-0938, SC-0939, SC-0942, SC-0978, SC-0988, SC-0992, SC-0996, SC-1130, SC-1166, SC-1167, SC-1172, SC-1187, SC-1195, SC-1261

**T5** (38): SC-0310, SC-0394, SC-0405, SC-0406, SC-0630, SC-0631, SC-0632, SC-0633, SC-0850, SC-0854, SC-0866, SC-0882, SC-0900, SC-0906, SC-0911, SC-0915, SC-0920, SC-0950, SC-0952, SC-0954, SC-0960, SC-0964, SC-0980, SC-0990, SC-1025, SC-1081, SC-1089, SC-1122, SC-1129, SC-1144, SC-1177, SC-1185, SC-1186, SC-1200, SC-1205, SC-1250, SC-1255, SC-1268

**T6** (1): SC-0847

---

## Appendix A — Archetype gaps added to the plausibility whitelist

Pairs absent from `plausable_cross_patterns` that this analysis nonetheless treats as plausible, each with the application archetype that justifies it. Without these, the filter would remove several hundred further rows that describe perfectly ordinary applications.

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

Two entries — Calendar + Fitness and Fitness + Tasks — are now redundant, since §2.4 excludes every Fitness pairing from the test. They are retained in the list so that reversing §2.4 restores the previous behaviour exactly.

## Appendix B — Inventory of implausible pairings

Every service pairing that triggered a removal, with the number of removed rows it appears in. Counts cover the 181 removed rows only. Fitness pairings are absent by construction (§2.4). Useful as a constraint list if the generator is rebuilt: forbidding these pairs at generation time removes the need for this filter.

| Implausible pairing | Rows |
|---|---:|
| Analytics + Contacts | 19 |
| Contacts + YouTube | 17 |
| Analytics + Calendar | 15 |
| Admin + Analytics | 14 |
| Calendar + Photos | 14 |
| Calendar + Firebase | 13 |
| Analytics + Tasks | 10 |
| Calendar + Cloud Storage | 10 |
| Calendar + Compute | 10 |
| BigQuery + Chat | 9 |
| Chat + Cloud Storage | 8 |
| Firebase + Tasks | 8 |
| Calendar + Cloud | 7 |
| Chat + Firebase | 7 |
| Analytics + Chat | 6 |
| BigQuery + Tasks | 6 |
| AdSense + Tasks | 5 |
| Admin + Photos | 5 |
| Analytics + Forms | 5 |
| Compute + Tasks | 5 |
| AdSense + Calendar | 4 |
| AdSense + Contacts | 4 |
| Admin + YouTube | 4 |
| Blogger + Calendar | 4 |
| Chat + Compute | 4 |
| Forms + Photos | 4 |
| AdSense + Forms | 3 |
| Analytics + Classroom | 3 |
| Analytics + Photos | 3 |
| Cloud Storage + Tasks | 3 |
| Firebase + Keep | 3 |
| AdSense + Chat | 2 |
| Admin + Blogger | 2 |
| BigQuery + Calendar | 2 |
| Blogger + Chat | 2 |
| Blogger + Contacts | 2 |
| Blogger + Firebase | 2 |
| Blogger + Forms | 2 |
| Classroom + Photos | 2 |
| Cloud + Tasks | 2 |
| Forms + Keep | 2 |
| Forms + YouTube | 2 |
| AdSense + Admin | 1 |
| Analytics + Keep | 1 |
| BigQuery + Keep | 1 |
| Blogger + Classroom | 1 |
| Blogger + Cloud | 1 |
| Blogger + Cloud Storage | 1 |
| Blogger + Compute | 1 |
| Blogger + Tasks | 1 |
| Chat + Cloud | 1 |
| Compute + Keep | 1 |
| Keep + YouTube | 1 |

## Appendix C — Reproducibility

The decision is deterministic and depends on no random state. Inputs are the dataset, the curated `plausable_cross_patterns` list from the dataset-creation notebook, the family definitions in §2.2 rule 4, the archetype list in Appendix A, and the health exclusion in §2.4. Files produced alongside this report:

- `scope_guard_dataset008_keep_remove_decisions.csv` — every row with its KEEP/REMOVE decision, category, flagged pairs (health and non-health separately) and resolved services.
- `scope_guard_dataset008_filtered.csv` — the dataset with the 181 removed rows dropped, columns otherwise unchanged; 1664 rows survive.

Two switches change the outcome and nothing else:

- **Reinstating the health filter.** Remove rule 6 in §2.2. Fitness pairings become flags again; the 53 rows in §5.1 join the removal set and the 18 rows in §5.2 change category.
- **Restoring the previous report's behaviour.** Keep rule 6 but give health rows priority over T2–T6, which returns the 18 rows in §5.2 to the kept set.

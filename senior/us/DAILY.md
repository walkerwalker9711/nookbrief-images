# Mayor of Main St. 매일 1편 작업 순서 (2026-11-05 주인님 "하루에 한 건씩 영상 자동화")

매일 예약 작업(05:47 KST 시작)이 이 파일을 처음부터 끝까지 따른다. 주인님 11-05: "매일 아침 07시에 대본 올려줘" →
대본(한국어 대사표)은 07:00 KST 전에 스레드에 올리고, 바로 렌더로 넘어간다(고칠 줄을 말하면 그 줄만 다시).
작업 브랜치는 `claude/project-thread-loj7pm`(senior-* 워크플로가 이 브랜치 push로도 돈다). 한국 채널은
`claude/project-thread-9sna6x`에서 따로 돌고 `senior/drafts/*-kr-*`, `senior/kr/`는 건드리지 않는다.
push 전에 꼭 `git pull --rebase origin claude/project-thread-loj7pm`.

## 0. 시작 점검
- `git fetch origin claude/project-thread-loj7pm claude/project-thread-9sna6x && git checkout -B claude/project-thread-loj7pm origin/claude/project-thread-loj7pm`
  그다음 `git merge --no-commit origin/claude/project-thread-9sna6x`(공용 스크립트 받기). senior/*/request, senior/samples/el_request 는 반드시 이 브랜치 것을 유지(`git checkout --ours`)해야 한국 편 업로드·렌더가 다시 돌지 않는다(11-06 한 번 겹쳐 돌았음).
- `senior/us/episodes.csv` 마지막 줄. 오늘 줄이 이미 있으면 그 편 마무리만.
- 어제 편이 scheduled인데 `upload_result.json`이 없으면 업로드 실패 → 원인부터.
- 크레딧: `senior/samples/el_request`에 `music check` push → `senior/samples/music_credits_check.txt`.
  2,500 아래면 렌더하지 않고 주인님께 한 줄(돈 드는 결정은 주인님 몫, 한국 스레드와 같은 계정).

## 1. 장르 (감동 2 : 사건 1)
- episodes.csv로 순서를 잇는다(감동, 감동, 사건 …). 11-04 감동, 11-05 감동 → 11-06 사건.
- 감동: 보도된 미국 실화만. 낯선 사람의 친절, 가족·부부, 이웃·상인·배달기사, 평생 모은 돈 기부, 참전용사, 아이·학생.
  경찰 미담은 최근 3편 중 1편 이하. 구조는 첫 줄 궁금증 → 시간 순서 → 끝에 밝혀지는 이유/반전.
- 사건: 조난·구조 / 미제사건 해결(DNA, 피해자 익명·범행 장면 X) / 재난·사고 생존 / 기막힌 검거 / 노인 대상 사기(조부모 사기, 기프트카드, 로맨스 스캠 등).
- 금지: 정치·선거·정치인, 총기 논쟁, 건강·의학 정보, 투자 권유, 지어낸 사연, 최근 30편과 같은 사건.
- 2개 이상 매체(지역 방송·NPR·AP·CBS 등)가 보도한 사연만. 실명 인터뷰 인용이 있는 것을 고른다(대사가 사람 말처럼 들림).

## 2. 소재와 기사 원문
- WebSearch로 후보 3개 → 첫 3초 훅이 가장 센 것 하나.
- 원문: `senior/channel/request`에 `us fetch <url> <url> ...` push → `senior/research/articles/`.

## 3. 대본 (script.json)
- 먼저 읽기: `senior/us/prompt.md`(Mayor 실화 드라마 + Two checks), `/mnt/project-files/NookBrief_자동화/SNS_글쓰기_규칙.md`.
- 직전 편 `senior/drafts/<어제>-us-drama/script.json`을 틀로 `senior/drafts/<오늘>-us-drama/script.json`.
  모든 scene의 speaker는 "host", 누가 말하는지는 role(캐릭터 id 또는 "내레이션"). sources는 [{name,url}].
- 해설은 Mayor(30대). 실제 인물의 보도된 말은 그대로 살린다(문법이 틀려도). 끝은 구독·공유 부탁 없이 본인 말이나 여운 한 줄.
- 설명란: 해시태그3 / 따옴표 훅 / 요약 2~3문장 / #mayorofmainst + 2개 / Source: 매체 이름(링크 X) / "Retold with AI voice & visuals".
  tags에 "Pops Knows" 금지(옛 이름). 편마다 내용 태그 1개 바꿈.
- 한국어 대사표: `/mnt/project-files/시니어쇼츠/미국_<N>편_대본_<YYYYMMDD>.md`(표 + 렌더 전 점검 + AI 티 점검 + 미국 입말 점검에서 고친 곳 줄별).
- 4번 점검을 통과하면 07:00 KST 전에 스레드에 대본 알림 1번(사연 3줄 + 대사표 attached_outputs + "고칠 줄은 말씀만, 렌더 시작").

- 새 역할 목소리가 필요하면(예: 미국 할머니) 대본 알림에 후보 링크(docs/preview/us/<이름>_N.mp3, Pages)를 같이 올리고, 주인님이 고른 뒤 `audition us save <역할> <번호>` → voices.json us에 저장 → 렌더.

- 11-06 해설 목소리 시험: 낮은 톤 후보 4개를 들어 본 주인님 "지금이 제일 나은 것 같다" → 지금 Mayor 목소리(rns7LXWBZ3RFXg9MK2qN, 속도 1.0) 유지. 후보는 저장하지 않음.

## 4. 렌더 전 점검 (하나라도 걸리면 고치고 다시)
1. 길이: 1편 기준 초당 14.8자 → 2분 50초(약 2,500자) 이하, 1분 이상.
2. 숫자는 숫자로 쓴다(자막도 숫자). 단어로 쓴 숫자는 caption_words.
3. 목소리: host(Mayor 30대), elder_m(80~90대 남), adult_m(중년 남), adult_f(여), adult_m2(두 번째 남).
   같은 편 같은 성별·나이대 둘이면 voice_pitch로 구분. 70~80대 여성 목소리는 아직 없음 → 필요하면 오디션(`audition us old_f`) 후 주인님 선택.
4. 인물이 나오는 장면은 cast에 모두. 멀리 있는 인물은 "shown from the waist up". 기준 그림과 나이가 다른 회상은 cast 비우고 모습 직접 적기.
5. Two checks(AI 티, 미국 입말) 통과.
6. 사람이 없어야 하는 장면(cast 비움)은 image_prompt 맨 앞에 "No people anywhere in the picture."를 쓴다. 끝에만 쓰면 엉뚱한 젊은 남녀가 그려짐(11-06, 11-07 두 번).

## 5. 렌더
- `senior/drafts/request`에 `us drama @<오늘> rerender` → push. senior-draft(약 20분).
  `gh api repos/walkerwalker9711/nookbrief-images/actions/workflows/senior-draft.yml/runs?per_page=3`로 백그라운드 대기, 실패 시 get_job_logs.

## 6. 렌더 후 점검
- 장면 그림 전부를 한 장으로 펼쳐 본다: 얼굴·나이·옷 일관성, 팔다리·손 빠짐, 한 장면 같은 인물 두 번, 여러 칸, 글자·로고.
  걸린 장면은 scene<N>.jpg 지우고 image_prompt 고쳐 다시 rerender(바뀐 것만, 목소리 캐시).
- 길이 3분 이하, props.json 장면별 voice.
- 썸네일: `python3 senior/us/brand/thumb.py <scene> "<줄1>" "<줄2>" "<빨간 띠>" "<태그>" senior/drafts/<오늘>-us-drama/thumb.jpg`.
- 미리보기(주인님 11-05 "다운받지 말고 브라우저에서 보게"): `ffmpeg -i video.mp4 -vf scale=540:-2 -crf 30 -c:a aac -b:a 96k senior/drafts/<오늘>-us-drama/preview.mp4`.
  GitHub Pages는 9sna6x 브랜치 docs/에서만 나가므로, 미리보기·썸네일만 그 브랜치에 올린다:
  `git fetch origin claude/project-thread-9sna6x && git worktree add <스크래치>/wt origin/claude/project-thread-9sna6x`,
  `docs/preview/us-<MMDD>.mp4`, `docs/preview/us-<MMDD>-thumb.jpg` 복사 → commit → `git pull --rebase origin claude/project-thread-9sna6x` → `git push origin HEAD:claude/project-thread-9sna6x`(docs/preview 말고는 건드리지 않음).
  1~2분 뒤 열림: https://walkerwalker9711.github.io/nookbrief-images/preview/us-<MMDD>.mp4 , …/preview/us-<MMDD>-thumb.jpg
  주인님께는 raw 다운로드 링크 대신 이 github.io 링크만 보낸다.

## 7. 예약 업로드
- 11-05 주인님 "2편 바로 올리라고": "올려"는 예약이 아니라 즉시 공개. 업로드 방식은 주인님 선택을 따른다(11-05 카드 "자동 업로드, 보류만 말하기" / "미리보기 보고 올려" / "대본·영상 둘 다 확인"). 선택 전이거나 "올려" 방식이면 미리보기를 보내고 주인님 "올려"를 받은 뒤에만 uploads/request를 push한다.
- upload.json에 `"publish_at"` = 미국 동부 저녁 7시 = 오늘 09:00 KST(`<오늘 KST 날짜>T00:00:00Z`, 서머타임 기간 3~11월 초엔 08:00 KST `T23:00:00Z` 전날). 그 시각이 이미 지났거나 30분도 안 남았으면 다음 날 같은 시각. tags 확인.
- `senior/uploads/request`에 폴더 → push. 비공개로 올라가고 그 시각에 자동 공개.
- upload_result.json 확인 → episodes.csv 오늘 줄(status scheduled) → push.

## 8. 주인님께 알림 (스레드 한 번, 80단어 안팎)
- 제목, 사연 한 줄, 출처, 길이, 미리보기, 한국어 대사표(attached_outputs), 공개 시각(KST), 유튜브 주소.
- "고칠 곳은 공개 전에 말씀해 주세요. '취소'면 비공개로 돌려요."
- 취소: upload.json `"privacy": "private"` → uploads/request 다시 push. 수정: 고쳐 다시 렌더 → 기존 private, 새 폴더 <오늘>-us-drama2로 다시.
- 주인님 지적은 그날 `senior/us/prompt.md`나 이 파일에 규칙으로.

## 9. 격주 월요일 (주인님께 2주마다 장르별 조회수 보고 약속, 11-05)
- `senior/channel/request`에 `us stats` → 장르별 조회수 → 비율 한 줄 보고.

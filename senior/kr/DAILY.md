# 한국이장님 매일 1편 작업 순서 (2026-11-05 주인님 "하루에 한 건씩 영상 자동화")

매일 예약 작업(06:23 KST)이 이 파일을 따른다. 11-05 주인님 "매일 아침 07시에 대본 올려줘": 0~4단계를 끝내고
07:00쯤 스레드에 대본(장면별 대사표 파일 + 요약)을 올린 뒤, 주인님이 "만들어"(또는 고칠 곳)라고 하면 5단계부터 진행한다. 작업 브랜치는 `claude/project-thread-9sna6x`
(senior-* 워크플로가 이 브랜치 push로만 돈다). 미국 채널(Mayor of Main St.)은 다른 스레드 담당이라
`senior/drafts/*-us-*`, `senior/us/`는 건드리지 않는다. 같은 request 파일을 쓰므로 push 전에 꼭 `git pull --rebase`.

## 0. 시작 점검
- `git fetch origin claude/project-thread-9sna6x && git checkout -B claude/project-thread-9sna6x origin/claude/project-thread-9sna6x`
- `senior/kr/episodes.csv` 마지막 줄을 본다. 오늘 날짜 줄이 이미 있으면 그 편을 이어서 마무리만 한다.
- 어제 편이 `scheduled`인데 upload_result.json이 없으면 업로드 실패 → 원인부터 고친다.
- 목소리 크레딧: `senior/samples/el_request`에 `music check` push → `senior/samples/music_credits_check.txt`.
  남은 크레딧이 2,000 아래면 렌더하지 말고 주인님께 한 줄로 알린다(돈이 드는 일이라 주인님 결정).

## 1. 장르 정하기 (감동 2 : 사건 1)
- episodes.csv 최근 줄로 순서를 잇는다: 사건 다음 감동, 감동, 그다음 사건.
- 감동: 보도된 실화만. 가족·부부 사연, 이웃·상인·기사님 미담, 평생 모은 돈 기부, 군인·소방관·의료진, 어린이·학생.
  경찰 미담은 최근 3편 중 1편 이하(episodes.csv police 칸). 구조는 가족 이야기 + 마지막에 밝혀지는 이유.
- 사건: ①조난·구조 ②미제사건 해결(DNA 등) ③재난·사고 생존 ④기막힌 범죄 검거 ⑤사기(전세사기·로맨스스캠·리딩방 등) 를 돌려 쓴다.
  episodes.csv kind 칸으로 직전 사건 종류와 겹치지 않게. 살인은 미제사건 해결 틀로만(범행 장면 X, 피해자 익명).
- 금지: 정치·역사 논란(4·3, 5·18, 이념, 정치인), 건강·의학 정보, 투자 권유, 지어낸 사연. 최근 30편과 같은 사건 금지.

## 2. 소재 고르기와 기사 원문
- WebSearch로 후보 3개를 찾고, 첫 3초 훅이 가장 센 것 하나를 고른다(트렌드 보드 trends/latest.json도 참고).
- 기사 원문은 이 환경에서 언론사가 막혀 있으니 `senior/channel/request`에 `kr fetch <url> <url> ...` push →
  senior-channel 워크플로가 `senior/research/articles/`에 저장. 보도 2곳 이상을 맞춰 본다.

## 3. 대본 (script.json)
- 먼저 읽기: `senior/kr/prompt.md`(쓰는 사람·말투·웹툰 드라마 편), `/mnt/project-files/NookBrief_자동화/SNS_글쓰기_규칙.md`(AI 티 점검표).
- 직전 편 `senior/drafts/<어제>-kr-drama/script.json`을 틀로 복사해 `senior/drafts/<오늘>-kr-drama/script.json`을 새로 쓴다.
  필드: pillar(감동 실화/사건 실화), topic, title(#실화), mood(touching/alert), music(직전과 다른 곡, video/music_lib/),
  case_tag, sources[{name,url}], description(아래 형식), tags, fact_notes, characters[id,label,voice,look], format "drama",
  voice_tempo, caption_words, scenes[kind,speaker,line,delivery,caption,hot,image_prompt,cast,phone,...], ko_review.
- 첫 0~3초 = 결과·반전 한 줄, 그 뒤는 시간 순서. 대사 위주, 이어 주는 말로 인과를 잇는다. 공적 인물은 깍듯한 존칭.
  끝은 구독·공유 부탁 없이 여운 한 줄. 자막은 넷플릭스식(한 줄 16자 안팎).
- 설명란: 해시태그3 / 따옴표 훅 / ▶ 요약 3줄 / 해시태그 / 📰 출처(이름만, 주소 링크 금지) / 맨 밑 "※ AI 음성·그림으로 재구성".
- upload.json: channel kr, title, description, tags, made_with_ai true, video video.mp4,
  `publish_at` = 오늘 18:00 KST(`YYYY-MM-DDT09:00:00Z`). 18시가 이미 지났으면 다음 정시.

## 4. 렌더 전 점검 (크레딧 아끼기, 하나라도 걸리면 고치고 다시)
1. 길이: 직전 편 초당 글자 수로 예상 → 2분 50초 이하, 1분 이상(틱톡 리워드). 길면 해설을 줄이거나 voice_tempo.
2. 한글로 풀어 쓴 숫자·영문은 caption_words에 모두(화면 자막은 숫자).
3. 인물마다 목소리 겹치지 않게: 60~65세 여성 mid_f, 70대+ 여성 old_f, 60~70대 남성 old_m, 90대 남성 elder_m,
   같은 편 남자 둘이면 adult_m2. 아이·무리도 characters에 넣어 기준 그림.
4. 인물이 나오는 장면은 cast에 모두 쉼표로. 멀리 있는 인물은 "shown from the waist up". 몽타주는 "ONE single full-frame picture, not a grid".
5. AI 티 점검표 5개 통과(SNS_글쓰기_규칙.md).

## 5. 렌더
- `senior/drafts/request`에 `kr drama @<오늘> rerender` (앞줄에 # 메모) → push. senior-draft 워크플로(약 15~25분)가
  그림·목소리·영상을 만들어 같은 브랜치에 push. `gh api repos/walkerwalker9711/nookbrief-images/actions/workflows/senior-draft.yml/runs?per_page=3`로
  백그라운드에서 끝나길 기다린다. 실패하면 mcp__github__get_job_logs로 원인을 보고 고친다.

## 6. 렌더 후 점검
- 장면 그림 전부를 한 장으로 펼쳐(PIL) Read로 본다: 얼굴·나이·옷 일관성, 팔다리·손 빠짐, 한 장면에 같은 인물 두 번, 여러 칸 만화, 글자.
  걸린 장면은 scene<N>.jpg를 지우고 image_prompt를 고쳐 다시 `kr drama @<오늘> rerender`(바뀐 것만 다시 그림, 목소리는 캐시).
- 영상 길이(3분 이하), 자막 프레임 몇 장, props.json 장면별 voice 역할 확인.
- 썸네일: `python3 senior/kr/brand/make_brand.py thumb <얼굴이 잘 보이는 scene> "<줄1>" "<줄2>" "<작은 줄>" "<태그>" senior/drafts/<오늘>-kr-drama/thumb.jpg`
  (빨간 띠 y≈620이 얼굴을 가리지 않는 장면).
- 미리보기: `ffmpeg -i video.mp4 -vf scale=540:-2 -crf 30 -c:a aac -b:a 96k docs/preview/<MMDD>-drama.mp4` → push
  (https://walkerwalker9711.github.io/nookbrief-images/preview/<MMDD>-drama.mp4).

## 7. 예약 업로드
- `senior/uploads/request`에 `senior/drafts/<오늘>-kr-drama` → push. upload.py가 비공개로 올리고 18:00 KST에 자동 공개.
- upload_result.json(video_id, publish_at) 확인 → episodes.csv에 오늘 줄 추가(status scheduled) → push.

## 8. 주인님께 알림 (스레드 한 번)
- 제목, 장르·사건 종류, 출처, 길이, 미리보기 링크, 썸네일 링크, 공개 시각, 유튜브 주소, 틱톡용 raw 영상 링크
  (https://github.com/walkerwalker9711/nookbrief-images/raw/claude/project-thread-9sna6x/senior/drafts/<오늘>-kr-drama/video.mp4).
- "고칠 곳이 있으면 18시 전에 말씀해 주세요. '취소'라고 하시면 비공개로 돌려요." 한 줄.
- 주인님이 취소하면: upload.json에 `"privacy": "private"` → uploads/request 다시 push. 고쳐 달라면 고쳐서 다시 렌더 →
  기존 영상은 private로 내리고 새 폴더 이름(<오늘>-kr-drama2)으로 다시 올린다.
- 주인님 지적은 그날 바로 `senior/kr/prompt.md`나 이 파일에 규칙으로 남긴다.

## 9. 매주 월요일 추가
- `senior/channel/request`에 `kr stats` → senior/research/stats/로 장르별 조회수 → 감동:사건 비율이 맞는지 한 줄 보고.

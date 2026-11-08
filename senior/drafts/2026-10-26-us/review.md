# Pops Knows 초안 2026-10-26

- 기둥: Scam / 주제: Fake USPS delivery texts demanding an address correction and card payment
- 제목: Pops Sends the Delivery Scam to the Wrong Inbox
- 목소리: elevenlabs

## 대본
1. [hook] This is USPS. Your package can't be delivered because your address is incomplete.  ·  화면 글자: Fake delivery meets the wrong grandpa
2. [phone] Use this redelivery link to update your address and pay the fee.  ·  화면 글자: There's the bait
   - 폰 화면 (+1 (202) 555-0148): USPS: Your package cannot be delivered due to an incomplete address. Update your address and pay the redelivery fee: https://parcel-update.example/redelivery
3. [talk] That redelivery link? Let me get it to the right department.  ·  화면 글자: Special delivery
4. [talk] Just enter your card details. Then we can release your package.  ·  화면 글자: An address needs a card?
5. [talk] Funny. My street address doesn't have an expiration date.  ·  화면 글자: Explain that one
6. [talk] Pay now, or your package goes back!  ·  화면 글자: Now comes the pressure
7. [twist] Your redelivery link already went to 7726 with your text, and I blocked you. Nice try, pal.  ·  화면 글자: Returned to spam
8. [talk] Wait, you forwarded WHAT?  ·  화면 글자: Wrong inbox, buddy
9. [steps] Real life, kid: don't reply or tap. Forward to 7726; check delivery at USPS dot com.  ·  화면 글자: Skip the conversation
   - O Don't reply or tap the link.
   - O Forward the scam text to 7726.
   - O Open USPS.com yourself to check tracking.
10. [outro] Send your folks this before their next package text.  ·  화면 글자: Give your folks a heads-up

## 한국어 검토본
1. 사기꾼: 우체국입니다. 주소가 불완전해서 고객님 소포를 배송할 수 없습니다.
2. 사기꾼: 이 재배송 링크에서 주소를 수정하고 수수료를 내세요.
3. Pops: 그 재배송 링크 말이지? 담당 부서로 잘 보내줘야겠구먼.
4. 사기꾼: 카드 정보만 입력하세요. 그러면 소포를 보내드릴 수 있습니다.
5. Pops: 이상하네. 우리 집 주소에는 유효기간이 없는데.
6. 사기꾼: 지금 결제하지 않으면 소포가 반송됩니다!
7. Pops: 네 재배송 링크는 문자째로 벌써 7726에 보냈고, 네 번호도 차단했어. 어림없다, 이 친구야.
8. 사기꾼: 잠깐, 뭘 전달했다고요?
9. Pops: 실제로는 말이다, 얘야. 답장도 링크 클릭도 하지 마. 7726으로 전달하고, 배송은 USPS 닷컴에 직접 들어가 확인해.
10. Pops: 부모님께 다음 택배 문자가 오기 전에 이 영상 보내드려.

## 숫자 출처
선정: 제공된 최근 7일 트렌드의 'scam text'에서 미국 시청자에게 맞는 USPS 사칭 문자를 골랐다. USPS 사칭 문자 자체의 이번 주 검색량이나 급증 여부는 별도로 확인하지 못했으므로 최신 유행·급증이라는 표현은 쓰지 않았다.
장면 1~2: 배송 문제를 내세워 링크로 유인하는 USPS 사칭 문자 수법은 USPIS 공식 경고에 근거한다. 대사는 실제 문자의 직접 인용이 아니라 수법을 설명하는 만화 재연이다. ([uspis.gov](https://www.uspis.gov/news/scam-article/smishing-package-tracking-text-scams))
장면 2·4: 주소 오류나 배송 문제를 미끼로 삼는 문자와 카드 정보를 수집하는 피싱 사이트는 Censys가 2026년 6월 12일 공개한 직접 조사에서 확인했다. 조사 통계나 피해액은 대본에 넣지 않았다. ([censys.com](https://censys.com/blog/following-a-usps-smishing-kit-through-censys-dns-data/))
장면 3·5~8: 등장인물의 대화와 신고 완료 반전은 교육용 만화 연출이며 실제 피해 사례나 실제 신고 기록으로 제시하지 않는다. 문자 대화를 의인화한 것으로, 시청자에게 사기꾼과 대화하라고 권하지 않는다.
장면 7·9의 7726: 연도별 통계가 아니라 미국 스팸 문자 신고용 단축번호다. 의심 문자를 전달하는 방법은 USPIS와 FTC가 안내한다. ([uspis.gov](https://www.uspis.gov/news/scam-article/smishing-package-tracking-text-scams))
장면 7의 차단은 Pops가 자기 휴대전화에서 직접 차단했다는 연출이다. 신고 즉시 통신사가 번호를 차단하거나 사이트를 폐쇄했다고 주장하지 않는다. FTC는 휴대전화와 통신사를 통한 스팸 차단 방법을 안내한다. ([consumer.ftc.gov](https://consumer.ftc.gov/articles/how-recognize-and-report-spam-text-messages?trk=public_post-text&utm_source=openai))
장면 9: 답장·링크 클릭을 피하고 USPS.com에 직접 방문해 배송을 확인하라는 행동은 USPIS 공식 안내에 근거한다. ([uspis.gov](https://www.uspis.gov/news/scam-article/smishing-package-tracking-text-scams))
화면의 발신번호는 재연용 가상 번호이며 .example 링크는 실제 접속용 주소가 아니다. 자막에는 출처명을 넣지 않고 sources의 자료를 별도 출처 푸터에 사용한다. 약 130단어로, 연기 호흡을 포함해 50~55초를 목표로 한다.

- USPIS: https://www.uspis.gov/news/scam-article/smishing-package-tracking-text-scams
- FTC: https://consumer.ftc.gov/articles/how-recognize-and-report-spam-text-messages?trk=public_post-text
- Censys: https://censys.com/blog/following-a-usps-smishing-kit-through-censys-dns-data/

## 설명란
A cartoon dramatization of a fake delivery text, not a real exchange.
Kid, don't reply or tap. Send this to your folks.
Sources:
USPIS: https://www.uspis.gov/news/scam-article/smishing-package-tracking-text-scams
FTC: https://consumer.ftc.gov/articles/how-recognize-and-report-spam-text-messages?trk=public_post-text
Censys: https://censys.com/blog/following-a-usps-smishing-kit-through-censys-dns-data/
AI voice & visuals

태그: Pops Knows, scam text, USPS text scam, delivery scam, smishing

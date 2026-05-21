-----------------------------------
[1] menus
---

---

손님용 메뉴 기본 정보를 저장하는 테이블

관계:

- recipes 와 1:1 관계

컬럼:

- id: uuid, primary key
- created_at: timestamptz, not null
- updated_at: timestamptz, not null
- category: menuCategory enum, nullable
- name: varchar, nullable
- name_en: varchar, nullable
- description: varchar, nullable
- price: int4, nullable
- taste_note: varchar, nullable
- abv: numeric, nullable
- tags: jsonb, nullable
- is_signature: bool, nullable

category enum:

- cocktail
- whisky
- non-alcohol
- highball
- side

설명:

- 손님이 QR 메뉴판에서 보는 정보 중심
- 메뉴 이름, 설명, 가격, 맛 표현, 도수 등을 저장
- 현재는 일반 메뉴 가격만 menus.price 에 저장
- 위스키 샷/바틀 구조는 추후 menu_prices 테이블로 확장 예정

---

## [2] glass_types

잔 종류를 관리하는 마스터 테이블

관계:

- recipes 와 1:N 관계

컬럼:

- id: uuid, primary key
- created_at: timestamptz, not null
- updated_at: timestamptz, not null
- code: varchar, not null, unique
- name_ko: varchar, not null
- name_en: varchar, nullable
- description: text, nullable
- is_active: boolean, not null, default true

설명:

- 운영자가 잔 종류를 직접 추가/수정 가능
- code 는 시스템 내부 식별값
- 삭제보다 is_active=false 비활성화 운영을 선호

예시 데이터:

- hurricane_glass
- martini_glass
- long_drink_glass
- shot_glass
- double_shot_glass
- margarita_glass
- rocks_glass
- old_fashioned_glass

---

## [3] recipes

메뉴별 레시피 기본 정보를 저장하는 테이블

관계:

- menus 와 1:1 관계
- glass_types 와 N:1 관계
- recipe_steps 와 1:N 관계

컬럼:

- id: uuid, primary key
- created_at: timestamptz, not null
- updated_at: timestamptz, not null
- menu_id: uuid, not null, unique
- glass_type_id: uuid, nullable
- garnish: varchar, nullable
- mixing_method: varchar, not null
- notes: text, nullable

Foreign Key:

- menu_id -> menus.id
- glass_type_id -> glass_types.id

설명:

- 메뉴 하나당 레시피 하나 구조
- 어떤 잔을 사용하는지 연결
- 제조 방식, 가니쉬, 메모 저장

mixing_method 예시:

- build
- stir
- shake
- shake + double strain
- stir + strain

설명:

- mixing_method 는 enum 이 아니라 varchar 사용
- 실제 바 운영에서는 표현이 유동적이라 자유 입력 방식 사용

---

## [4] recipe_steps

문장형 제조법(step)을 저장하는 테이블

관계:

- recipes 와 N:1 관계

컬럼:

- id: uuid, primary key
- created_at: timestamptz, not null
- updated_at: timestamptz, not null
- recipe_id: uuid, not null
- step_order: int4, not null
- instruction: text, not null

Foreign Key:

- recipe_id -> recipes.id

설명:

- 한 레시피는 여러 제조 단계를 가짐
- 직원이 바로 읽고 따라 만들 수 있는 문장형 구조
- 재료량 + 제조방식 + 순서를 자연어로 저장

예시:

1. 보드카 30ml + 블루 30ml + 라임쥬스 20ml 쉐이킹
2. 나머지는 사이드로 채워서 스터

---

## [삭제된 구조]

recipe_ingredients 테이블은 제거함

제거 이유:

- 재료 리스트와 제조 문장을 동시에 관리하면 입력 중복 발생
- 실제 현장에서는 문장형 제조법이 더 직관적
- 어드민 입력 복잡도를 줄이기 위해 제거

현재는:

- recipes
- recipe_steps

중심의 완전 문장형 레시피 구조 사용

---

## [현재 관계 구조]

menus 1 : 1 recipes

glass_types 1 : N recipes

recipes 1 : N recipe_steps

---

## [Cascade 정책]

recipes.menu_id

- ON DELETE CASCADE 선호

recipe_steps.recipe_id

- ON DELETE CASCADE 선호

recipes.glass_type_id

- CASCADE 사용하지 않음
- RESTRICT 또는 is_active=false 운영 선호

---

## [향후 확장 예정]

1. menu_prices

- 위스키 샷/바틀 가격 구조 대응 예정

예상 구조:

- menu_id
- price_type
- price
- display_order

price_type 예시:

- default
- shot
- bottle

2. inventory system

- 재고관리 시스템 추가 고려 중
- 술 / 리큐르 / 음료 재고 관리 목적

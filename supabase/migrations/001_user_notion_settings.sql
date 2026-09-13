-- =============================================================
-- 사용자별 Notion 저장 설정
--
-- 적용 방법: Supabase 대시보드 → SQL Editor 에 붙여넣고 Run
--
-- 목적: "Notion 저장" 버튼이 서버에 고정된 페이지 하나가 아니라
--       각 사용자가 지정한 본인 Notion 페이지에 저장되도록 한다.
-- =============================================================

create table if not exists public.user_notion_settings (
  user_id      uuid        primary key references auth.users (id) on delete cascade,
  access_token text        not null,
  page_id      text        not null,
  updated_at   timestamptz not null default now()
);

comment on table  public.user_notion_settings is '사용자별 Notion 연동 설정 (개인 integration 토큰 + 대상 페이지)';
comment on column public.user_notion_settings.access_token is 'Notion internal integration token. 소유자 본인만 접근 가능(RLS).';
comment on column public.user_notion_settings.page_id      is '블록을 append 할 Notion 페이지 ID (32자 hex)';

-- RLS: 본인 행만 읽기/쓰기 가능
alter table public.user_notion_settings enable row level security;

drop policy if exists "본인 설정 조회" on public.user_notion_settings;
create policy "본인 설정 조회"
  on public.user_notion_settings for select
  using (auth.uid() = user_id);

drop policy if exists "본인 설정 생성" on public.user_notion_settings;
create policy "본인 설정 생성"
  on public.user_notion_settings for insert
  with check (auth.uid() = user_id);

drop policy if exists "본인 설정 수정" on public.user_notion_settings;
create policy "본인 설정 수정"
  on public.user_notion_settings for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists "본인 설정 삭제" on public.user_notion_settings;
create policy "본인 설정 삭제"
  on public.user_notion_settings for delete
  using (auth.uid() = user_id);

-- updated_at 자동 갱신
create or replace function public.touch_user_notion_settings()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_touch_user_notion_settings on public.user_notion_settings;
create trigger trg_touch_user_notion_settings
  before update on public.user_notion_settings
  for each row execute function public.touch_user_notion_settings();

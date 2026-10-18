-- CONTROLE DE ESTOQUE — 7 LOJAS
-- Execute no SQL Editor do Supabase em um projeto novo.
-- Depois crie usuários em Authentication > Users e associe cada UUID em public.profiles.
-- Para funcionárias sem e-mail pessoal, use nome_de_usuario@estoque.invalid como e-mail interno
-- e ative Auto Confirm User. No app, elas digitam apenas nome_de_usuario.

create extension if not exists pgcrypto;

create table if not exists public.stores (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  created_at timestamptz not null default now()
);

create table if not exists public.profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  display_name text not null,
  role text not null check (role in ('admin', 'staff')),
  store_id uuid references public.stores(id) on delete restrict,
  created_at timestamptz not null default now(),
  constraint profile_store_role_check check (
    (role = 'admin' and store_id is null) or
    (role = 'staff' and store_id is not null)
  )
);

create table if not exists public.stock_entries (
  id uuid primary key default gen_random_uuid(),
  store_id uuid not null references public.stores(id) on delete restrict,
  user_id uuid not null references auth.users(id) on delete restrict,
  product text not null check (product in ('Marmitas', 'Refrigerantes', 'Pudins', 'Águas')),
  quantity_remaining integer not null check (quantity_remaining >= 0),
  photo_path text,
  notes text,
  created_at timestamptz not null default now()
);

create index if not exists stock_entries_store_product_time_idx
  on public.stock_entries (store_id, product, created_at desc);
create index if not exists stock_entries_user_time_idx
  on public.stock_entries (user_id, created_at desc);

-- Funções SECURITY DEFINER para consultar o perfil sem recursão de políticas RLS.
create or replace function public.current_user_role()
returns text
language sql
stable
security definer
set search_path = public
as $$
  select role from public.profiles where user_id = auth.uid()
$$;

create or replace function public.current_user_store_id()
returns uuid
language sql
stable
security definer
set search_path = public
as $$
  select store_id from public.profiles where user_id = auth.uid()
$$;

revoke all on function public.current_user_role() from public;
grant execute on function public.current_user_role() to authenticated;
revoke all on function public.current_user_store_id() from public;
grant execute on function public.current_user_store_id() to authenticated;

alter table public.stores enable row level security;
alter table public.profiles enable row level security;
alter table public.stock_entries enable row level security;

-- Privilégios SQL: as políticas RLS abaixo limitam quais linhas cada papel pode acessar.
grant select on public.stores to authenticated;
grant select on public.profiles to authenticated;
grant select, insert, update, delete on public.stock_entries to authenticated;

-- Remove políticas com os mesmos nomes para permitir reexecutar este script.
drop policy if exists "stores_admin_all" on public.stores;
drop policy if exists "stores_staff_own_store" on public.stores;
drop policy if exists "profiles_read_self_or_admin" on public.profiles;
drop policy if exists "profiles_admin_manage" on public.profiles;
drop policy if exists "entries_read_admin_or_own_store" on public.stock_entries;
drop policy if exists "entries_read_admin_only" on public.stock_entries;
drop policy if exists "entries_staff_insert_own_store" on public.stock_entries;
drop policy if exists "entries_admin_update" on public.stock_entries;
drop policy if exists "entries_admin_delete" on public.stock_entries;

create policy "stores_admin_all" on public.stores
for all to authenticated
using (public.current_user_role() = 'admin')
with check (public.current_user_role() = 'admin');

create policy "stores_staff_own_store" on public.stores
for select to authenticated
using (id = public.current_user_store_id());

create policy "profiles_read_self_or_admin" on public.profiles
for select to authenticated
using (user_id = auth.uid() or public.current_user_role() = 'admin');

create policy "profiles_admin_manage" on public.profiles
for all to authenticated
using (public.current_user_role() = 'admin')
with check (public.current_user_role() = 'admin');

create policy "entries_read_admin_only" on public.stock_entries
for select to authenticated
using (public.current_user_role() = 'admin');

create policy "entries_staff_insert_own_store" on public.stock_entries
for insert to authenticated
with check (
  public.current_user_role() = 'staff'
  and user_id = auth.uid()
  and store_id = public.current_user_store_id()
);

create policy "entries_admin_update" on public.stock_entries
for update to authenticated
using (public.current_user_role() = 'admin')
with check (public.current_user_role() = 'admin');

create policy "entries_admin_delete" on public.stock_entries
for delete to authenticated
using (public.current_user_role() = 'admin');

-- Bucket privado para fotos (não use bucket público para fotos de estoque).
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('stock-photos', 'stock-photos', false, 8388608, array['image/jpeg','image/png','image/webp'])
on conflict (id) do update set public = false, file_size_limit = 8388608,
  allowed_mime_types = array['image/jpeg','image/png','image/webp'];

drop policy if exists "photos_staff_upload_own_store_folder" on storage.objects;
drop policy if exists "photos_read_admin_or_own_store" on storage.objects;
drop policy if exists "photos_read_admin_only" on storage.objects;
drop policy if exists "photos_admin_delete" on storage.objects;

-- Caminho de cada foto: <store_uuid>/<user_uuid>/<nome-do-arquivo>
create policy "photos_staff_upload_own_store_folder" on storage.objects
for insert to authenticated
with check (
  bucket_id = 'stock-photos'
  and public.current_user_role() = 'staff'
  and (storage.foldername(name))[1] = public.current_user_store_id()::text
  and (storage.foldername(name))[2] = auth.uid()::text
);

create policy "photos_read_admin_only" on storage.objects
for select to authenticated
using (bucket_id = 'stock-photos' and public.current_user_role() = 'admin');

create policy "photos_admin_delete" on storage.objects
for delete to authenticated
using (bucket_id = 'stock-photos' and public.current_user_role() = 'admin');

-- Cadastre as sete lojas (nomes editáveis depois, se necessário).
insert into public.stores (name) values
  ('Loja 1'), ('Loja 2'), ('Loja 3'), ('Loja 4'), ('Loja 5'), ('Loja 6'), ('Loja 7')
on conflict (name) do nothing;

-- IMPORTANTE:
-- 1) No Supabase, crie primeiro o usuário administrador em Authentication > Users.
-- 2) Copie o UUID desse usuário e rode um INSERT em public.profiles, por exemplo:
-- insert into public.profiles (user_id, display_name, role, store_id)
-- values ('UUID-DO-USUARIO-ADMIN', 'Administrador', 'admin', null);
-- 3) Crie cada funcionária em Authentication > Users e associe a uma loja:
-- insert into public.profiles (user_id, display_name, role, store_id)
-- values ('UUID-DA-FUNCIONARIA', 'Nome da funcionária', 'staff',
--         (select id from public.stores where name = 'Loja 1'));
-- 4) Só pessoas com role='admin' podem administrar lojas e perfis pelo banco.

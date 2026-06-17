--
-- PostgreSQL database dump
--

\restrict WAzsCB6GQy5OO4ekwo8P0uDgMRHgLYlH3Awc3bbrxsH8Zqo8CZZj1ZquAqnSSrH

-- Dumped from database version 16.4 (Debian 16.4-1.pgdg120+2)
-- Dumped by pg_dump version 18.4 (Ubuntu 18.4-1.pgdg24.04+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: roletype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.roletype AS ENUM (
    'ADMIN',
    'CUSTOMER',
    'PARTNER'
);


--
-- Name: usertype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.usertype AS ENUM (
    'SUPERADMIN',
    'CUSTOMER',
    'PARTNER'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: auth_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_sessions (
    session_id uuid NOT NULL,
    user_id character varying NOT NULL,
    jti character varying NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone
);


--
-- Name: dpdp_consents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dpdp_consents (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    consented_at timestamp with time zone NOT NULL,
    version character varying NOT NULL,
    source character varying NOT NULL,
    created_at timestamp with time zone
);


--
-- Name: email_templates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.email_templates (
    id uuid NOT NULL,
    slug character varying NOT NULL,
    description character varying,
    subject character varying NOT NULL,
    html_body text NOT NULL,
    is_active boolean NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: enrollment_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.enrollment_history (
    id uuid NOT NULL,
    enrollment_id uuid NOT NULL,
    user_id uuid NOT NULL,
    partner_id uuid NOT NULL,
    from_plan_id uuid,
    to_plan_id uuid NOT NULL,
    action character varying NOT NULL,
    changed_by character varying NOT NULL,
    note character varying,
    changed_at timestamp with time zone
);


--
-- Name: family_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.family_members (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    name character varying NOT NULL,
    relation character varying NOT NULL,
    gender character varying,
    dob date,
    coverage_type character varying,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: member_enrollments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.member_enrollments (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    partner_id uuid NOT NULL,
    plan_id uuid NOT NULL,
    status character varying NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: member_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.member_profiles (
    user_id uuid NOT NULL,
    gender character varying,
    dob date,
    address_line character varying,
    address_city character varying,
    address_state character varying,
    address_pin character varying,
    preferred_language character varying NOT NULL,
    channel_email boolean NOT NULL,
    channel_whatsapp boolean NOT NULL,
    channel_voice boolean NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: membership_plans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.membership_plans (
    id uuid NOT NULL,
    name character varying NOT NULL,
    tagline character varying NOT NULL,
    info_text text,
    price bigint NOT NULL,
    cycle character varying NOT NULL,
    plan_type character varying NOT NULL,
    status character varying NOT NULL,
    color character varying,
    popular boolean NOT NULL,
    is_deleted boolean NOT NULL,
    benefit_family integer NOT NULL,
    benefit_slots integer NOT NULL,
    benefit_claim character varying NOT NULL,
    benefit_aiqa boolean NOT NULL,
    benefit_aicalls boolean NOT NULL,
    benefit_voice character varying NOT NULL,
    benefit_vault boolean NOT NULL,
    benefit_rm boolean NOT NULL,
    benefit_concierge boolean NOT NULL,
    benefit_teleconsult_sessions integer NOT NULL,
    benefit_hospital_cash boolean NOT NULL,
    benefit_wellness_sessions integer NOT NULL,
    benefit_emergency_assist boolean NOT NULL,
    benefit_legal_assist boolean NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: nominees; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nominees (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    name character varying NOT NULL,
    relation character varying NOT NULL,
    share_percent integer NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.notifications (
    id uuid NOT NULL,
    recipient_user_id uuid NOT NULL,
    type character varying NOT NULL,
    title character varying NOT NULL,
    body character varying,
    ref_id character varying,
    ref_type character varying,
    is_read boolean NOT NULL,
    created_at timestamp with time zone
);


--
-- Name: otp_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.otp_log (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    email character varying NOT NULL,
    otp_code character varying NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    is_used boolean NOT NULL,
    attempts integer NOT NULL,
    created_at timestamp with time zone
);


--
-- Name: partner_plans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.partner_plans (
    id uuid NOT NULL,
    partner_id uuid NOT NULL,
    plan_id uuid NOT NULL,
    created_at timestamp with time zone
);


--
-- Name: partners; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.partners (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    name character varying NOT NULL,
    partner_type character varying NOT NULL,
    city character varying,
    status character varying NOT NULL,
    api_key character varying,
    api_rate_limit integer NOT NULL,
    is_deleted boolean NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: policies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.policies (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    partner_id uuid NOT NULL,
    policy_number character varying,
    insurer character varying,
    sum_insured bigint,
    start_date date,
    end_date date,
    status character varying NOT NULL,
    ai_confidence integer,
    extracted_fields jsonb,
    is_deleted boolean NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    policy_type_id uuid NOT NULL,
    storage_key character varying,
    file_name character varying
);


--
-- Name: policy_family_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.policy_family_members (
    id uuid NOT NULL,
    policy_id uuid NOT NULL,
    family_member_id uuid NOT NULL,
    created_at timestamp with time zone
);


--
-- Name: policy_types; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.policy_types (
    id uuid NOT NULL,
    name character varying NOT NULL,
    code character varying NOT NULL,
    description character varying,
    is_active boolean NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roles (
    id uuid NOT NULL,
    role_name character varying NOT NULL,
    role_type public.roletype NOT NULL,
    is_active boolean NOT NULL
);


--
-- Name: user_activity; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_activity (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    first_login_at timestamp with time zone,
    last_login_at timestamp with time zone,
    login_count integer NOT NULL,
    has_logged_in boolean NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone
);


--
-- Name: user_roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_roles (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    role_id uuid NOT NULL,
    assigned_by uuid,
    is_active boolean NOT NULL,
    created_at timestamp with time zone
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid NOT NULL,
    email character varying NOT NULL,
    name character varying,
    user_type public.usertype NOT NULL,
    is_active boolean NOT NULL,
    is_deleted boolean NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    mobile_no character varying
);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
4873e1f01972
\.


--
-- Data for Name: auth_sessions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.auth_sessions (session_id, user_id, jti, expires_at, created_at) FROM stdin;
c863138a-ea9d-4292-9b05-4b629b592bc4	213c0630-327d-4b98-92c1-529d128fed8c	4cdd9f46-572f-4968-9b09-0c12c487aaa9	2026-06-15 15:15:46.431425+00	2026-06-15 14:45:03.675803+00
0045b561-1ffc-4b43-a276-65fae1a19448	213c0630-327d-4b98-92c1-529d128fed8c	81dbe0ec-4bad-4500-8020-bb56ade727e6	2026-06-15 15:18:17.250865+00	2026-06-15 14:48:17.252031+00
aa8928a4-ed6c-4779-98f8-bc689463ba48	213c0630-327d-4b98-92c1-529d128fed8c	bffc1a98-ad9c-44e0-8fed-089372f07efd	2026-06-16 11:39:10.832705+00	2026-06-16 11:09:10.834351+00
19ea5445-2be0-49a5-81c0-2fdf8242f797	213c0630-327d-4b98-92c1-529d128fed8c	f914ce94-c619-445a-ab4d-93d414e42e3a	2026-06-16 11:39:26.858955+00	2026-06-16 11:09:26.859317+00
ee04970d-a1cd-4c4c-9c64-fd365a329e5c	213c0630-327d-4b98-92c1-529d128fed8c	e1a87e5b-0d5f-4eaa-9702-6cac498910d9	2026-06-16 11:39:41.211747+00	2026-06-16 11:09:41.212609+00
d6dc5d85-e359-4938-80f8-350cc7d43da5	213c0630-327d-4b98-92c1-529d128fed8c	5f78ef5c-63cc-408a-920e-7880259d3b71	2026-06-16 11:45:51.738802+00	2026-06-16 11:15:51.739192+00
f236c608-ba55-4259-8f7a-2cffa54c26dc	213c0630-327d-4b98-92c1-529d128fed8c	87bd313a-23e7-4ea7-8117-1ea5c8e61aa3	2026-06-16 11:46:04.560318+00	2026-06-16 11:16:04.560843+00
265b695f-6092-4578-bb55-6dd23eb55cca	213c0630-327d-4b98-92c1-529d128fed8c	0ea6217b-204c-48b8-965a-8540589eeef2	2026-06-16 11:48:24.182387+00	2026-06-16 11:18:24.18501+00
f3a9ec3e-af2b-480b-9eee-b8ea957c6bc0	2d42b993-d396-4489-96b4-44baffa94828	5e4e464c-33df-4e6b-8574-5fe6d01434d9	2026-06-16 11:48:43.453962+00	2026-06-16 11:18:43.454347+00
fa6ee36f-badc-4a46-ba81-78edac4029ea	c0b50711-22bf-4ea6-a7d7-f932591705fb	efa246f4-6afd-44f3-bb28-d38ebd0e42a0	2026-06-16 11:49:11.164434+00	2026-06-16 11:19:11.165057+00
2cd5112b-ae10-4afa-92a9-a926a413a706	c0b50711-22bf-4ea6-a7d7-f932591705fb	23eb3c20-999f-4475-acaf-2c0b960b64fb	2026-06-16 11:49:27.733322+00	2026-06-16 11:19:27.733749+00
47b51232-b6d1-4b81-b498-41fd39e0ec45	213c0630-327d-4b98-92c1-529d128fed8c	5e29f024-af8b-44f9-876c-b47d2350dbe4	2026-06-16 11:49:29.490312+00	2026-06-16 11:19:29.490769+00
aa1a0f1d-403e-4384-90aa-897143f6410b	c0b50711-22bf-4ea6-a7d7-f932591705fb	bd2f3bcb-4b20-45d9-803c-62c1ca03a6e2	2026-06-16 12:15:38.525168+00	2026-06-16 11:45:38.526114+00
6150d210-dd9a-4fd7-982c-0e602ad6df2f	213c0630-327d-4b98-92c1-529d128fed8c	8e58261b-194c-42fa-a8f2-59e3da1ef420	2026-06-16 12:15:38.801831+00	2026-06-16 11:45:38.802275+00
8616b147-c6d9-4fa0-b852-bbd862596ddc	2d42b993-d396-4489-96b4-44baffa94828	5ace3018-1c03-4822-a8fa-77beadafaf23	2026-06-16 12:15:39.074155+00	2026-06-16 11:45:39.074496+00
0eb0083d-dba4-43e0-b6b3-03a0a27be257	213c0630-327d-4b98-92c1-529d128fed8c	0c580283-8ef2-43d0-8ae4-1f5df2403a36	2026-06-16 12:16:04.624288+00	2026-06-16 11:46:04.624746+00
8c63093a-03cc-4510-b05f-641470fac4c5	2d42b993-d396-4489-96b4-44baffa94828	ab1eafa7-3b70-4954-ba18-cd7cd1c47ee8	2026-06-16 12:16:05.669502+00	2026-06-16 11:46:05.669936+00
289caa81-a68c-4097-b148-6c60888a131f	c0b50711-22bf-4ea6-a7d7-f932591705fb	27e96bff-01a8-4df4-8adb-4ba977ff8a05	2026-06-16 12:17:50.663096+00	2026-06-16 11:47:50.663383+00
56ce55d1-9f78-41d6-930e-587543515627	213c0630-327d-4b98-92c1-529d128fed8c	43e7922a-6c43-4a9e-bf6e-a3a958c33b29	2026-06-16 12:17:51.185989+00	2026-06-16 11:47:51.18633+00
d61f18a2-fcd9-46ac-b4b0-89b9b962998d	2d42b993-d396-4489-96b4-44baffa94828	60db7f30-f4e2-408c-a886-6fcfb3696102	2026-06-16 12:17:51.709453+00	2026-06-16 11:47:51.709806+00
27846823-e406-4650-b2a8-28febd6a5c3a	c0b50711-22bf-4ea6-a7d7-f932591705fb	b3ec41e0-cd09-40df-bd99-8121d372ed25	2026-06-16 12:25:03.510268+00	2026-06-16 11:55:03.511517+00
bf3857d5-43f6-4310-8d55-26496db6de43	213c0630-327d-4b98-92c1-529d128fed8c	4ef603d1-1180-4cae-b9d0-10be03f19ac8	2026-06-16 12:25:04.028733+00	2026-06-16 11:55:04.029105+00
1eadadcd-fbff-4698-b0fa-2d099985944f	2d42b993-d396-4489-96b4-44baffa94828	f828d9c6-5e0b-4b63-9052-23c3c4071793	2026-06-16 12:25:04.548824+00	2026-06-16 11:55:04.549152+00
1de38200-3c53-4618-91fa-f6bd02ad8123	c0b50711-22bf-4ea6-a7d7-f932591705fb	04938454-3e2f-40f3-8c7b-ba5419e08984	2026-06-16 12:38:43.076503+00	2026-06-16 12:08:43.077677+00
a86b14d1-1992-44bc-8070-ca794cfba4ab	213c0630-327d-4b98-92c1-529d128fed8c	cc1c08e3-911d-4d95-b9b6-288e1d107326	2026-06-16 12:38:43.600979+00	2026-06-16 12:08:43.601435+00
0f157189-5af6-4f50-9dc0-2fdbfb8c4e1c	2d42b993-d396-4489-96b4-44baffa94828	8ea39cd1-a573-4494-b4e3-9b556c4b6c0b	2026-06-16 12:38:44.148814+00	2026-06-16 12:08:44.149154+00
00ff9f67-67f5-4014-9049-8fca7e2e11ab	016370aa-3ed0-4aea-a065-f865aed9e245	81df7479-b47a-4e5b-80dd-cfd7879929a9	2026-06-16 13:12:47.464779+00	2026-06-16 12:42:47.465143+00
641229b6-1304-451e-82d6-33f82103508b	016370aa-3ed0-4aea-a065-f865aed9e245	00dd4bc3-8ecc-4122-aa07-1e6bac0016ea	2026-06-16 13:13:43.3485+00	2026-06-16 12:43:43.348949+00
766ea499-8bd5-4da7-bda1-9d0737fa1567	016370aa-3ed0-4aea-a065-f865aed9e245	8d3b61dc-88bd-4573-8b22-2278b9005d75	2026-06-16 13:17:28.325786+00	2026-06-16 12:47:28.327023+00
87295c12-cc51-4f74-b8ec-b44b63a1554a	016370aa-3ed0-4aea-a065-f865aed9e245	dccc9c07-e8be-43e7-8f79-ab8eae32c9f9	2026-06-16 13:18:25.344362+00	2026-06-16 12:48:25.345641+00
33f6a673-c497-47b6-8414-6656ac056463	b5569ec9-1a95-4969-9a97-a714e82c5ba7	c59c518c-686e-4fd0-a64c-e7f5e1caf7c8	2026-06-16 13:18:26.01089+00	2026-06-16 12:48:26.011388+00
767539f0-cc6c-4710-b1c6-e8346ffb8194	016370aa-3ed0-4aea-a065-f865aed9e245	1299d928-78d1-45dd-9623-00132581a185	2026-06-16 13:19:02.87844+00	2026-06-16 12:49:02.879847+00
075d3ecd-c616-4489-8fd8-4fd46daf1f02	016370aa-3ed0-4aea-a065-f865aed9e245	0489b36d-779e-47dc-9d4a-5e490f9998ba	2026-06-16 13:19:54.088534+00	2026-06-16 12:49:54.089885+00
e7c0536b-e9b6-4ca6-9a7e-624975ece1c2	016370aa-3ed0-4aea-a065-f865aed9e245	9cf74b40-29be-46fd-bbe5-2b70bb92d8b7	2026-06-16 13:20:54.311551+00	2026-06-16 12:50:54.31198+00
c15c70a6-1f8e-4cf0-b3b7-3eed330e25d8	b677f283-5b8d-42ae-bcb0-0af5808697c3	9c407c98-02f5-4666-af98-55d3657079be	2026-06-16 13:20:54.964263+00	2026-06-16 12:50:54.964665+00
dd813319-dd0d-466f-81ba-ab6d24b97718	3f663e54-b4bb-4fa7-abf3-1b632a9f7893	0e5b46cd-4846-4a7b-b58e-5a08214f1307	2026-06-16 13:20:58.822909+00	2026-06-16 12:50:58.823267+00
6e6d3bdd-90a7-412e-a877-88f78080b413	213c0630-327d-4b98-92c1-529d128fed8c	10eba44b-1386-4260-ae8a-11dad03959d5	2026-06-16 14:01:35.192496+00	2026-06-16 13:31:35.193179+00
8ee3d1b9-51c8-4941-a725-5088d0931f16	213c0630-327d-4b98-92c1-529d128fed8c	b76acd75-c3de-4969-86d1-fb6d7d3ec337	2026-06-16 14:02:20.285924+00	2026-06-16 13:32:20.286246+00
e0477bd5-0723-49e0-ba78-c5a8b257209c	213c0630-327d-4b98-92c1-529d128fed8c	727a323b-1972-4f37-84cd-3508a570dff4	2026-06-16 14:03:59.540029+00	2026-06-16 13:33:59.540493+00
555a2e82-fd5d-4b83-bda2-fc0ba808246e	213c0630-327d-4b98-92c1-529d128fed8c	bbf3cedc-2ff6-4600-a4db-03a6fe9b5ed9	2026-06-16 14:05:20.36811+00	2026-06-16 13:35:20.368465+00
23be1b22-ac4f-4064-80bb-7d6bb2ddbc1b	213c0630-327d-4b98-92c1-529d128fed8c	cb0c356d-bf84-47b4-95e5-3f20015fc63d	2026-06-16 14:06:54.334911+00	2026-06-16 13:36:54.335231+00
0ebd3fd4-d2b4-4479-a215-2d8d98d4749f	2d42b993-d396-4489-96b4-44baffa94828	9de291f8-b07a-431b-ba53-b5e3f1b0aef5	2026-06-16 14:07:41.527089+00	2026-06-16 13:37:41.527423+00
65e77c02-9b33-4629-8ad7-fb781c1d6e59	c0b50711-22bf-4ea6-a7d7-f932591705fb	d9df72ba-032e-4ea9-98e8-8e9dfc145f2a	2026-06-16 14:08:03.605512+00	2026-06-16 13:38:03.606003+00
3161cc9b-7fd9-4e6f-bfa5-f8afa2ae1fd5	213c0630-327d-4b98-92c1-529d128fed8c	ed43e596-76ef-4cbe-8325-3881cc39f2f8	2026-06-16 14:16:15.405882+00	2026-06-16 13:46:15.407593+00
b9222a52-6fd9-44bd-943d-c32409134839	213c0630-327d-4b98-92c1-529d128fed8c	ed5b7cb4-16af-4177-b1ac-32104925195a	2026-06-16 14:17:08.792776+00	2026-06-16 13:47:08.793115+00
77d828a8-2fe3-4699-8191-546c5601b073	213c0630-327d-4b98-92c1-529d128fed8c	58c97e9a-0896-43c4-acf3-c4ae5305cb26	2026-06-16 14:17:52.553397+00	2026-06-16 13:47:52.553882+00
e5da8074-ba18-4140-88eb-03119c71eaca	213c0630-327d-4b98-92c1-529d128fed8c	82658f23-2146-46b3-bdfe-05d82d048cd9	2026-06-16 14:22:10.791179+00	2026-06-16 13:52:10.791962+00
7e31a1e1-1998-4622-bf57-e3a2f8e8b0c1	213c0630-327d-4b98-92c1-529d128fed8c	c9bb73bc-eed1-4b7f-8e53-25dea0831922	2026-06-16 14:23:06.459516+00	2026-06-16 13:53:06.459813+00
a42f8d5a-5eaa-454a-90fe-5ae172a039b0	213c0630-327d-4b98-92c1-529d128fed8c	4aff3a96-33c5-426a-a7d9-22f9a0543f0a	2026-06-16 14:26:18.269681+00	2026-06-16 13:56:18.270025+00
74c119cf-0b4b-4fb9-bd39-b6f22a60e2ff	213c0630-327d-4b98-92c1-529d128fed8c	b972c4be-c3ad-4108-a980-e9e7013280b6	2026-06-16 14:27:13.078451+00	2026-06-16 13:57:13.078791+00
08cba3ee-193c-4a13-9ddb-b52c46d0227a	213c0630-327d-4b98-92c1-529d128fed8c	9508b2d1-a76c-4459-8e59-c9d234a2d291	2026-06-16 14:27:29.391821+00	2026-06-16 13:57:29.392268+00
af33845b-1bb4-421f-8992-da9a0e19159f	2d42b993-d396-4489-96b4-44baffa94828	29711500-3a09-4dcf-a0c2-34a79c52a7f3	2026-06-16 14:27:49.989744+00	2026-06-16 13:57:49.990106+00
eb10a4a5-9598-4064-8e39-3734ea47616e	c0b50711-22bf-4ea6-a7d7-f932591705fb	979e53a7-fb83-446d-81ac-40cceef87bc0	2026-06-16 14:27:53.638561+00	2026-06-16 13:57:53.638966+00
75ca4848-6632-41db-8a43-2a1af6322662	2d42b993-d396-4489-96b4-44baffa94828	ce320a2a-0e8e-4d90-8b7e-248a6376badc	2026-06-16 14:28:05.391573+00	2026-06-16 13:58:05.391882+00
8d980ccb-9cfa-4bed-ad5d-c8b59299114f	2d42b993-d396-4489-96b4-44baffa94828	81216ba7-db5e-49ab-ba7f-a6c033669ab5	2026-06-16 14:28:18.497446+00	2026-06-16 13:58:18.497853+00
ce87b8b9-f06f-4e5a-aa9c-d98b389d6809	c0b50711-22bf-4ea6-a7d7-f932591705fb	1ad32730-df2e-43d0-beb5-25d50d7cf93f	2026-06-16 14:29:02.746979+00	2026-06-16 13:59:02.747474+00
28a334a7-1075-432c-9234-b411e6a9dd12	c0b50711-22bf-4ea6-a7d7-f932591705fb	640053de-406f-471c-8d4f-5b3e5e6e5c96	2026-06-16 14:31:31.138463+00	2026-06-16 14:01:31.138775+00
c31927e9-6d30-4678-9d11-f4ca2724c162	c0b50711-22bf-4ea6-a7d7-f932591705fb	c4335ad7-1f81-4c06-8664-b7e26ec1f6b5	2026-06-16 14:31:50.19477+00	2026-06-16 14:01:50.195243+00
d922ab7c-92c1-4e6f-aa71-afe07d4b672d	c0b50711-22bf-4ea6-a7d7-f932591705fb	358a4b88-e7d1-4b45-8e8b-4b2905275df6	2026-06-16 14:32:07.198941+00	2026-06-16 14:02:07.199295+00
d0bc1e0e-b6f4-4d09-97a3-94ea9e9bebaf	213c0630-327d-4b98-92c1-529d128fed8c	4b504b0e-d91f-4f08-b1d7-915f51092b79	2026-06-16 14:34:09.000658+00	2026-06-16 14:04:09.001057+00
47d127c2-340e-4d83-80ad-e4bdbb086a12	c0b50711-22bf-4ea6-a7d7-f932591705fb	cdcc1f66-2dc9-4e0c-b6fe-c327d2f49e23	2026-06-16 14:34:12.117151+00	2026-06-16 14:04:12.117505+00
f7d6d9d1-38c0-4da1-be5a-fbc8d5cd71fd	213c0630-327d-4b98-92c1-529d128fed8c	161666f8-4877-47fc-a666-4908067a0f39	2026-06-16 14:37:56.559152+00	2026-06-16 14:07:56.559551+00
935e1c29-9ea1-4bf9-b7b0-e557508ff5cc	c0b50711-22bf-4ea6-a7d7-f932591705fb	802a6e98-5a32-4c51-9421-c72767cf0949	2026-06-16 14:38:00.355904+00	2026-06-16 14:08:00.356253+00
514ab559-df38-4e4e-b032-f69a297ae256	213c0630-327d-4b98-92c1-529d128fed8c	72754cb9-df43-44c9-b052-4af5ea64c711	2026-06-16 14:40:39.855933+00	2026-06-16 14:10:39.856355+00
fe671dc2-f8a0-4581-80b3-039655242905	213c0630-327d-4b98-92c1-529d128fed8c	3a80229d-2e95-43db-a718-cb009a040dd1	2026-06-16 14:40:49.367122+00	2026-06-16 14:10:49.367484+00
ef14f031-d22c-4279-a25d-7cfe90a1e61e	213c0630-327d-4b98-92c1-529d128fed8c	f148cd18-8f60-48a8-b3e0-562a2303e792	2026-06-16 14:41:01.14793+00	2026-06-16 14:11:01.14827+00
3c1b551a-b2ae-490c-b703-239f68eb3e34	2d42b993-d396-4489-96b4-44baffa94828	f9ae84a9-8302-42e4-9327-80d85cc8e91a	2026-06-16 14:41:51.210811+00	2026-06-16 14:11:51.211156+00
4af21187-8535-4e15-884c-ac3046ac83d0	cd32eb60-940a-4016-8a3d-1b3d251e3d27	f1b2689e-e57d-4b34-aa46-62d3c6dd737b	2026-06-17 13:42:20.010008+00	2026-06-17 13:12:20.010444+00
6dfb740b-2dd9-4cd3-b494-4f789e285620	83f2ce28-c466-4687-98f1-24ab2340d531	d352688f-078e-4fc3-b54a-c8261a5ecfbb	2026-06-16 14:46:23.439888+00	2026-06-16 14:16:23.440271+00
8992fe19-add5-4bea-a7c7-2c1d97641ea0	213c0630-327d-4b98-92c1-529d128fed8c	f42ee329-e545-4a40-815c-c9b7ab613ac7	2026-06-16 15:00:45.320176+00	2026-06-16 14:30:45.320518+00
7fe9760a-b5e8-4706-b2af-85ec97acbb66	c0b50711-22bf-4ea6-a7d7-f932591705fb	728a545d-cb17-4d09-9356-cf233b1c82b9	2026-06-16 15:18:33.694235+00	2026-06-16 14:48:33.694811+00
9b47e616-bc69-4897-916c-27413c3c1d2c	c620c95b-ccde-436c-87c6-da3e331ca0bf	12418681-75e5-463b-b980-ae4cc101d819	2026-06-17 18:49:12.154801+00	2026-06-17 18:19:12.155228+00
32353e3e-9976-4234-9e22-899cc38aa12f	213c0630-327d-4b98-92c1-529d128fed8c	a1ed87e2-2f5c-4943-af45-713e35a5206c	2026-06-16 16:19:45.216168+00	2026-06-16 15:49:45.216881+00
e5831b20-9ec7-4cf8-b46a-8d8c30197958	213c0630-327d-4b98-92c1-529d128fed8c	db98760a-5a2e-4cbd-8b7a-182872c07b6c	2026-06-17 07:25:38.137145+00	2026-06-17 06:55:38.137685+00
f62aa651-fc43-4dda-aeda-e510e797b429	cd32eb60-940a-4016-8a3d-1b3d251e3d27	18d8e13f-7661-49c0-b40b-d075d93a7b0e	2026-06-17 10:09:47.409622+00	2026-06-17 09:37:45.081657+00
0e5529be-4c43-4a18-911c-ddcf51bd5a73	4444a2f9-ad30-4414-8491-f4025b6f76ba	1a487dbb-9c02-491c-83bf-fa716aed5f14	2026-06-17 10:15:44.239396+00	2026-06-17 09:45:44.239777+00
ca11ca21-4f1e-4297-99ae-5fae81cc7efa	38eb24db-e6e4-4ade-8c8d-ac9942c6d9eb	7a8f2036-a304-4a2a-b34e-292d35f0acd3	2026-06-17 11:24:23.209758+00	2026-06-17 10:28:02.896356+00
\.


--
-- Data for Name: dpdp_consents; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.dpdp_consents (id, user_id, consented_at, version, source, created_at) FROM stdin;
4fea3155-73f4-469c-acb5-072111a69c53	3f663e54-b4bb-4fa7-abf3-1b632a9f7893	2026-06-16 12:51:18.69583+00	1.0	portal	2026-06-16 12:51:18.697119+00
c6a071ad-636e-4e04-8afe-901eb04daec0	83f2ce28-c466-4687-98f1-24ab2340d531	2026-06-16 15:01:33.365385+00	1.0	member_portal	2026-06-16 15:01:33.367367+00
\.


--
-- Data for Name: email_templates; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.email_templates (id, slug, description, subject, html_body, is_active, created_at, updated_at) FROM stdin;
a5e056a9-23bf-44ea-b82b-cd0376395751	otp_login	OTP sent during login	Your EasyClaims Login OTP	<html><body>\n<p>Hello,</p>\n<p>Your one-time password (OTP) for EasyClaims login is:</p>\n<h2 style="letter-spacing:4px;font-family:monospace;">{{ otp }}</h2>\n<p>This OTP is valid for {{ otp_expire_minutes }} minutes.</p>\n<p>If you did not request this, please ignore this email.</p>\n<p style="color:#888;font-size:12px;">— EasyClaims Team</p>\n</body></html>	t	2026-06-17 07:27:02.695817+00	2026-06-17 07:27:02.695821+00
896278a4-ee21-4129-ab7b-3297da9dc8e3	welcome_member	Sent to a new member when their account is created	Welcome to EasyClaims — Your Account is Ready	<html><body>\n<p>Hi {{ member_name }},</p>\n<p>Your EasyClaims account has been set up by <strong>{{ partner_name }}</strong>.</p>\n<p>You can now log in and manage your health insurance policies in one place.</p>\n<table style="border-collapse:collapse;margin:16px 0">\n  <tr><td style="padding:4px 12px 4px 0;color:#666">Login Email</td><td><strong>{{ email }}</strong></td></tr>\n  <tr><td style="padding:4px 12px 4px 0;color:#666">Login Method</td><td>OTP (One-Time Password sent to this email)</td></tr>\n</table>\n<p style="margin:20px 0">\n  <a href="{{ login_url }}" style="background:#0066cc;color:#fff;padding:10px 24px;text-decoration:none;border-radius:4px;">Login to EasyClaims</a>\n</p>\n<p style="color:#888;font-size:13px;">If you have any questions, reply to this email or contact your partner.</p>\n<p>— EasyClaims Team</p>\n</body></html>	t	2026-06-17 07:27:02.70842+00	2026-06-17 07:27:02.708423+00
09e6cb93-c3c8-41e7-8c71-9f6a4a3dc1c4	policy_uploaded_member	Sent to member when a policy is uploaded	Policy Uploaded — {{ policy_number }}	<html><body>\n<p>Dear {{ member_name }},</p>\n<p>Your <strong>{{ policy_type }}</strong> policy has been successfully uploaded to EasyClaims.</p>\n<table style="border-collapse:collapse;margin:16px 0">\n  <tr><td style="padding:4px 12px 4px 0;color:#666">Policy Number</td><td><strong>{{ policy_number }}</strong></td></tr>\n  <tr><td style="padding:4px 12px 4px 0;color:#666">Type</td><td>{{ policy_type }}</td></tr>\n  <tr><td style="padding:4px 12px 4px 0;color:#666">Status</td><td>Under Review</td></tr>\n</table>\n<p>Our team will review your document and update the status shortly.</p>\n<p>— EasyClaims Team</p>\n</body></html>	t	2026-06-17 07:27:02.712882+00	2026-06-17 07:27:02.712886+00
b04cd661-add3-4a75-9e96-7e4e302f1f49	policy_uploaded_partner	Sent to partner when a member uploads a policy	New Policy Uploaded by Member — {{ policy_number }}	<html><body>\n<p>Dear {{ partner_name }},</p>\n<p>A member under your account has uploaded a new policy document.</p>\n<table style="border-collapse:collapse;margin:16px 0">\n  <tr><td style="padding:4px 12px 4px 0;color:#666">Member</td><td><strong>{{ member_name }}</strong> ({{ member_email }})</td></tr>\n  <tr><td style="padding:4px 12px 4px 0;color:#666">Policy Number</td><td><strong>{{ policy_number }}</strong></td></tr>\n  <tr><td style="padding:4px 12px 4px 0;color:#666">Type</td><td>{{ policy_type }}</td></tr>\n  <tr><td style="padding:4px 12px 4px 0;color:#666">Status</td><td>Pending Review</td></tr>\n</table>\n<p>Log in to the partner portal to review the uploaded document.</p>\n<p>— EasyClaims System</p>\n</body></html>	t	2026-06-17 07:27:02.717043+00	2026-06-17 07:27:02.717047+00
42a5446e-d4b0-45a1-8ec5-38a1dfde4f5f	policy_uploaded_admin	Sent to admin when a policy is uploaded	[Admin] New Policy Upload — {{ policy_number }}	<html><body>\n<p>A new policy has been uploaded and requires review.</p>\n<table style="border-collapse:collapse;margin:16px 0">\n  <tr><td style="padding:4px 12px 4px 0;color:#666">Policy Number</td><td><strong>{{ policy_number }}</strong></td></tr>\n  <tr><td style="padding:4px 12px 4px 0;color:#666">Type</td><td>{{ policy_type }}</td></tr>\n  <tr><td style="padding:4px 12px 4px 0;color:#666">Member</td><td>{{ member_name }} ({{ member_email }})</td></tr>\n  <tr><td style="padding:4px 12px 4px 0;color:#666">Partner</td><td>{{ partner_name }}</td></tr>\n</table>\n<p>— EasyClaims System</p>\n</body></html>	t	2026-06-17 07:27:02.721367+00	2026-06-17 07:27:02.72137+00
65a10f86-3baa-469b-81ee-b55d51843ecb	plan_expiry_warning	Sent to member 2 days before plan expires	Your EasyClaims Plan Expires in {{ days_left }} Day{% if days_left != 1 %}s{% endif %}	<html><body>\n<p>Dear {{ member_name }},</p>\n<p>This is a reminder that your EasyClaims plan is expiring soon.</p>\n<table style="border-collapse:collapse;margin:16px 0;background:#fff8e1;border:1px solid #ffe082;border-radius:8px">\n  <tr><td style="padding:8px 16px;color:#666">Plan</td><td style="padding:8px 16px"><strong>{{ plan_name }}</strong></td></tr>\n  <tr><td style="padding:8px 16px;color:#666">Expiry Date</td><td style="padding:8px 16px"><strong style="color:#e65100">{{ end_date }}</strong></td></tr>\n  <tr><td style="padding:8px 16px;color:#666">Days Remaining</td><td style="padding:8px 16px"><strong>{{ days_left }} day{% if days_left != 1 %}s{% endif %}</strong></td></tr>\n</table>\n<p>Please contact your partner or log in to renew your plan before it expires.</p>\n<p>— EasyClaims Team</p>\n</body></html>	t	2026-06-17 07:27:02.725589+00	2026-06-17 07:27:02.725592+00
1bc25a50-0a59-4c0d-924c-0e0ad596c87e	plan_expired_member	Sent to member when their plan has expired	Your EasyClaims Plan Has Expired	<html><body>\n<p>Dear {{ member_name }},</p>\n<p>Your EasyClaims plan has expired. Please contact your partner to renew your plan and restore access.</p>\n<table style="border-collapse:collapse;margin:16px 0;background:#ffebee;border:1px solid #ffcdd2;border-radius:8px">\n  <tr><td style="padding:8px 16px;color:#666">Plan</td><td style="padding:8px 16px"><strong>{{ plan_name }}</strong></td></tr>\n  <tr><td style="padding:8px 16px;color:#666">Expired On</td><td style="padding:8px 16px"><strong style="color:#c62828">{{ end_date }}</strong></td></tr>\n</table>\n<p>— EasyClaims Team</p>\n</body></html>	t	2026-06-17 07:27:02.729873+00	2026-06-17 07:27:02.729877+00
98b89884-64b0-4038-b28c-9a43d409c508	plan_expired_partner	Sent to partner when a member's plan expires	Member Plan Expired — {{ member_name }}	<html><body>\n<p>Dear {{ partner_name }},</p>\n<p>A member's EasyClaims plan has expired and they may need renewal.</p>\n<table style="border-collapse:collapse;margin:16px 0">\n  <tr><td style="padding:4px 12px 4px 0;color:#666">Member</td><td><strong>{{ member_name }}</strong> ({{ member_email }})</td></tr>\n  <tr><td style="padding:4px 12px 4px 0;color:#666">Plan</td><td>{{ plan_name }}</td></tr>\n  <tr><td style="padding:4px 12px 4px 0;color:#666">Expired On</td><td><strong style="color:#c62828">{{ end_date }}</strong></td></tr>\n</table>\n<p>Log in to the partner portal to renew this member's enrollment.</p>\n<p>— EasyClaims System</p>\n</body></html>	t	2026-06-17 07:27:02.733431+00	2026-06-17 07:27:02.733434+00
59380d33-0ed9-46ed-b03c-47b6b0ec641b	plan_changed	Sent to member when their plan is changed	Your EasyClaims Plan Has Been Updated	<html><body>\n<p>Dear {{ member_name }},</p>\n<p>Your EasyClaims plan has been updated.</p>\n<table style="border-collapse:collapse;margin:16px 0">\n  <tr><td style="padding:4px 12px 4px 0;color:#666">Previous Plan</td><td>{{ old_plan }}</td></tr>\n  <tr><td style="padding:4px 12px 4px 0;color:#666">New Plan</td><td><strong>{{ new_plan }}</strong></td></tr>\n  <tr><td style="padding:4px 12px 4px 0;color:#666">Changed By</td><td>{{ changed_by }}</td></tr>\n</table>\n<p>If you did not expect this change, please contact your partner.</p>\n<p>— EasyClaims Team</p>\n</body></html>	t	2026-06-17 07:27:02.737334+00	2026-06-17 07:27:02.737337+00
5536245d-fd4a-4dee-be3e-067b68310aa4	enrollment_renewed	Sent to member when their enrollment is renewed	Your EasyClaims Plan Has Been Renewed	<html><body>\n<p>Dear {{ member_name }},</p>\n<p>Great news! Your EasyClaims plan has been renewed.</p>\n<table style="border-collapse:collapse;margin:16px 0;background:#e8f5e9;border:1px solid #c8e6c9;border-radius:8px">\n  <tr><td style="padding:8px 16px;color:#666">Plan</td><td style="padding:8px 16px"><strong>{{ plan_name }}</strong></td></tr>\n  <tr><td style="padding:8px 16px;color:#666">New Expiry Date</td><td style="padding:8px 16px"><strong style="color:#2e7d32">{{ end_date }}</strong></td></tr>\n</table>\n<p>— EasyClaims Team</p>\n</body></html>	t	2026-06-17 07:27:02.740951+00	2026-06-17 07:27:02.740954+00
\.


--
-- Data for Name: enrollment_history; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.enrollment_history (id, enrollment_id, user_id, partner_id, from_plan_id, to_plan_id, action, changed_by, note, changed_at) FROM stdin;
\.


--
-- Data for Name: family_members; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.family_members (id, user_id, name, relation, gender, dob, coverage_type, created_at, updated_at) FROM stdin;
58c4d17b-1fc4-4a42-a800-691a172dc961	c0b50711-22bf-4ea6-a7d7-f932591705fb	Priya Sharma	Spouse	F	\N	Health	2026-06-16 11:19:11.343096+00	2026-06-16 11:19:11.343098+00
c7e82460-fdad-412d-97e8-6611dec4f5b0	3f663e54-b4bb-4fa7-abf3-1b632a9f7893	Priya Test	Spouse	Female	1993-06-20	Health	2026-06-16 12:50:58.904267+00	2026-06-16 12:50:58.904271+00
0ecf9f79-29a1-4fc9-bce3-011e09c808e3	3f663e54-b4bb-4fa7-abf3-1b632a9f7893	Arjun Test	Son	Male	2018-03-10	Health	2026-06-16 12:50:58.915286+00	2026-06-16 12:50:58.915289+00
19dcca3c-abcc-4474-823f-a0cbdf96ca4c	83f2ce28-c466-4687-98f1-24ab2340d531	chinar	Parent	Female	2026-06-16	Life	2026-06-16 14:59:25.522928+00	2026-06-16 14:59:25.522934+00
10fb7608-47b1-4bb3-b0aa-2d7800127ce7	38eb24db-e6e4-4ade-8c8d-ac9942c6d9eb	Viraj	Other	Male	2026-06-16	Health	2026-06-17 10:29:21.689371+00	2026-06-17 10:29:21.689374+00
3d319947-ac58-4ff9-b5a3-20dcb440968f	38eb24db-e6e4-4ade-8c8d-ac9942c6d9eb	Kedar	Child	Male	2026-06-16	Health	2026-06-17 10:37:19.988138+00	2026-06-17 10:37:19.988141+00
b9846833-1575-41a1-8efd-0cb9f81accac	38eb24db-e6e4-4ade-8c8d-ac9942c6d9eb	suhass	Parent	Male	2014-05-01	Life	2026-06-17 10:37:48.048556+00	2026-06-17 10:37:48.04856+00
35f09344-8c69-4fdc-ba7a-e10c60af27c0	38eb24db-e6e4-4ade-8c8d-ac9942c6d9eb	Sahil	Parent	Other	2023-05-24	Health	2026-06-17 10:38:07.901065+00	2026-06-17 10:38:07.901069+00
6641a957-d53c-4463-8f2a-d7214b7a53f5	38eb24db-e6e4-4ade-8c8d-ac9942c6d9eb	Manish	Sibling	Male	2024-07-02	Accident	2026-06-17 10:38:29.762134+00	2026-06-17 10:38:29.762138+00
\.


--
-- Data for Name: member_enrollments; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.member_enrollments (id, user_id, partner_id, plan_id, status, start_date, end_date, created_at, updated_at) FROM stdin;
bb7b6045-f076-4b79-973a-b6f31889a88f	c0b50711-22bf-4ea6-a7d7-f932591705fb	6cd47d22-9412-46e5-ad7a-3a274d141f29	92150516-da43-41b1-8921-3a35b952060e	active	2026-06-16	2027-06-16	2026-06-16 11:18:24.330437+00	2026-06-16 11:19:28.326569+00
34588c87-36e5-4e3e-9f8f-cb884b56e465	3f663e54-b4bb-4fa7-abf3-1b632a9f7893	00dfeec1-f697-413a-93ed-f437a9cf9a53	c1e14f37-6d41-4fac-8c62-ea3b0e607ff8	active	2026-06-16	2027-06-16	2026-06-16 12:50:55.036242+00	2026-06-16 12:50:55.036245+00
3023dab7-23ae-4838-af28-4cf26ecfcfdb	83f2ce28-c466-4687-98f1-24ab2340d531	f25c2437-b295-4017-af89-83c477c10185	c1e14f37-6d41-4fac-8c62-ea3b0e607ff8	active	2026-06-16	2027-06-16	2026-06-16 14:16:04.546011+00	2026-06-16 15:25:17.664451+00
c10849e6-3719-4127-ae0d-0d7f4669bfa6	83f2ce28-c466-4687-98f1-24ab2340d531	00dfeec1-f697-413a-93ed-f437a9cf9a53	c1e14f37-6d41-4fac-8c62-ea3b0e607ff8	active	2026-06-16	2027-06-16	2026-06-16 15:27:00.565982+00	2026-06-16 15:27:00.565989+00
7d0bc6a1-851a-4f44-9ef0-cb6bd790fea0	38eb24db-e6e4-4ade-8c8d-ac9942c6d9eb	f25c2437-b295-4017-af89-83c477c10185	92150516-da43-41b1-8921-3a35b952060e	Active	2026-06-17	2027-06-17	2026-06-17 09:39:28.2117+00	2026-06-17 09:39:28.211704+00
9b98f854-2d47-4b89-aecf-54c34f6e38cf	38eb24db-e6e4-4ade-8c8d-ac9942c6d9eb	c93adfb1-c37a-4db3-8426-6e24c30101bf	82fee7bc-1f99-4132-bd31-718e1a661a37	Active	2026-06-17	2027-06-17	2026-06-17 10:27:08.549779+00	2026-06-17 10:27:08.549783+00
\.


--
-- Data for Name: member_profiles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.member_profiles (user_id, gender, dob, address_line, address_city, address_state, address_pin, preferred_language, channel_email, channel_whatsapp, channel_voice, created_at, updated_at) FROM stdin;
c0b50711-22bf-4ea6-a7d7-f932591705fb	\N	\N	\N	\N	\N	\N	English	t	f	f	2026-06-16 11:18:24.337302+00	2026-06-16 11:18:24.337306+00
3f663e54-b4bb-4fa7-abf3-1b632a9f7893	Male	1990-05-15	12 MG Road	Mumbai	Maharashtra	400001	English	t	t	f	2026-06-16 12:50:55.043778+00	2026-06-16 12:50:58.881731+00
83f2ce28-c466-4687-98f1-24ab2340d531	\N	\N	\N	\N	\N	\N	English	t	f	f	2026-06-16 14:16:04.555884+00	2026-06-16 14:16:04.555888+00
38eb24db-e6e4-4ade-8c8d-ac9942c6d9eb	Male	2010-01-06	Mumbai	Vasai	Maharashtra		English	t	f	f	2026-06-17 09:39:28.223831+00	2026-06-17 10:28:55.324184+00
\.


--
-- Data for Name: membership_plans; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.membership_plans (id, name, tagline, info_text, price, cycle, plan_type, status, color, popular, is_deleted, benefit_family, benefit_slots, benefit_claim, benefit_aiqa, benefit_aicalls, benefit_voice, benefit_vault, benefit_rm, benefit_concierge, benefit_teleconsult_sessions, benefit_hospital_cash, benefit_wellness_sessions, benefit_emergency_assist, benefit_legal_assist, created_at, updated_at) FROM stdin;
92150516-da43-41b1-8921-3a35b952060e	Secure	Complete protection for families	Full-family coverage with priority claim assistance.	2999	Annual	global	Active	var(--green-500)	t	f	4	6	Priority	t	t	English + Hindi	t	f	t	0	f	0	f	f	2026-06-16 10:21:54.722212+00	2026-06-16 10:21:54.722213+00
5f7f9533-8ee3-4b58-a41e-b1279e48952a	Total Care	Premium concierge membership	24x7 priority care with dedicated RM and concierge filing.	4999	Annual	global	Active	var(--blue-900)	f	f	6	12	Standard	t	t	English + Hindi	t	t	t	0	f	0	f	f	2026-06-16 10:21:54.722226+00	2026-06-16 10:21:54.722227+00
0f27135d-10f9-4b3d-9175-ef3991673a7b	Test Secure Plan 342a5630		\N	2999	Annual	global	Active	var(--blue-500)	f	f	2	3	Standard	t	f	English	t	f	f	0	f	0	f	f	2026-06-16 12:50:54.355609+00	2026-06-16 12:50:54.370136+00
82fee7bc-1f99-4132-bd31-718e1a661a37	Plan testing 2	Plan testing 2	\N	10110	Annual	partner	Active	var(--blue-500)	t	f	4	3	Standard	t	t	English	t	t	t	1	t	1	t	t	2026-06-16 15:47:42.959192+00	2026-06-17 10:18:33.746413+00
8c39e9b5-5491-43f5-a0a4-0415d275f2e6	Plan testing 1	testing marking	\N	100	Annual	partner	Active	var(--blue-500)	t	f	4	5	Standard	t	f	English	t	t	t	0	t	0	t	t	2026-06-16 15:37:05.27048+00	2026-06-17 10:18:35.460183+00
4058a851-b31e-4e6e-8940-671f5b2453a5	Test Secure Plan		\N	2999	Annual	global	Active	var(--blue-500)	f	f	2	3	Standard	t	f	English	t	f	f	0	f	0	f	f	2026-06-16 12:48:25.399839+00	2026-06-17 10:24:08.307845+00
c1e14f37-6d41-4fac-8c62-ea3b0e607ff8	Essential	Everyday cover for individuals	Get started with essential health membership coverage.	1499	Annual	global	Active	var(--blue-500)	f	f	2	3	Standard	t	t	English	t	t	t	0	t	0	t	t	2026-06-16 10:21:54.722192+00	2026-06-17 11:50:37.43221+00
\.


--
-- Data for Name: nominees; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.nominees (id, user_id, name, relation, share_percent, created_at, updated_at) FROM stdin;
fedb07f9-fef6-4176-8e1f-bddbb615e652	c0b50711-22bf-4ea6-a7d7-f932591705fb	Priya Sharma	Spouse	100	2026-06-16 11:19:11.376082+00	2026-06-16 11:19:11.376087+00
239eafbd-2f34-4477-91cd-36786c15469e	3f663e54-b4bb-4fa7-abf3-1b632a9f7893	Priya Test	Spouse	60	2026-06-16 12:50:58.936421+00	2026-06-16 12:50:58.936424+00
7615e772-db6e-4acc-8878-cdcb24626443	3f663e54-b4bb-4fa7-abf3-1b632a9f7893	Arjun Test	Son	40	2026-06-16 12:50:58.949009+00	2026-06-16 12:50:58.949011+00
\.


--
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.notifications (id, recipient_user_id, type, title, body, ref_id, ref_type, is_read, created_at) FROM stdin;
31f34d1b-9cc8-4faa-babb-abc55ea7d97d	213c0630-327d-4b98-92c1-529d128fed8c	policy_uploaded	[Admin] New Policy Upload — POL-2026-189101	Rahul Test Updated (member_342a5630@test.com) via Test Brokers Ltd 342a5630 uploaded a Health policy.	7702e8f8-5067-4335-b821-d11dcaf6a23e	policy	f	2026-06-16 12:51:05.887329+00
c3032503-3b3d-447e-bcb8-3993d0bc9a15	213c0630-327d-4b98-92c1-529d128fed8c	policy_uploaded	[Admin] New Policy Upload — POL-2026-285982	Rahul Test Updated (member_342a5630@test.com) via Test Brokers Ltd 342a5630 uploaded a Motor policy.	09fbc4a0-471b-4f1d-b8d6-599fe5f4ec03	policy	f	2026-06-16 12:51:15.755135+00
e5eb3b67-e6c1-49d7-978b-74391e689e58	b677f283-5b8d-42ae-bcb0-0af5808697c3	policy_uploaded	New Policy Uploaded — POL-2026-285982	Rahul Test Updated (member_342a5630@test.com) uploaded a Motor policy.	09fbc4a0-471b-4f1d-b8d6-599fe5f4ec03	policy	t	2026-06-16 12:51:13.572714+00
64d12cb3-43b7-4d79-9177-1f9c596e70ec	016370aa-3ed0-4aea-a065-f865aed9e245	policy_uploaded	[Admin] New Policy Upload — POL-2026-189101	Rahul Test Updated (member_342a5630@test.com) via Test Brokers Ltd 342a5630 uploaded a Health policy.	7702e8f8-5067-4335-b821-d11dcaf6a23e	policy	t	2026-06-16 12:51:08.808702+00
bcca9b67-ab81-4d3d-97ff-8da881652260	213c0630-327d-4b98-92c1-529d128fed8c	policy_uploaded	[Admin] New Policy Upload — POL-2026-111461	fsfs (chinarartak@gmail.com) via chinar uploaded a Health policy.	9dac6be6-b763-4692-9cf9-92e848d895cb	policy	f	2026-06-16 15:28:19.335055+00
1057cbde-e3b5-40eb-92bd-2a2b792138a7	016370aa-3ed0-4aea-a065-f865aed9e245	policy_uploaded	[Admin] New Policy Upload — POL-2026-111461	fsfs (chinarartak@gmail.com) via chinar uploaded a Health policy.	9dac6be6-b763-4692-9cf9-92e848d895cb	policy	f	2026-06-16 15:28:21.578052+00
f0829dd5-b043-41eb-860e-3310fa102c54	cd32eb60-940a-4016-8a3d-1b3d251e3d27	policy_uploaded	New Policy Uploaded — POL-2026-111461	fsfs (chinarartak@gmail.com) uploaded a Health policy.	9dac6be6-b763-4692-9cf9-92e848d895cb	policy	t	2026-06-16 15:28:17.098077+00
9260d079-146d-42bb-b4ce-b3b794fd5305	cd32eb60-940a-4016-8a3d-1b3d251e3d27	policy_uploaded	New Policy Uploaded — POL-2026-249943	Test chinar member (workmytemp@gmail.com) uploaded a Critical Illness policy.	c1bac8c3-1699-41ad-9e82-e3a374ba8974	policy	f	2026-06-17 10:55:26.501609+00
c84ca976-56f9-4a92-aa27-37e123ace964	213c0630-327d-4b98-92c1-529d128fed8c	policy_uploaded	[Admin] New Policy Upload — POL-2026-249943	Test chinar member (workmytemp@gmail.com) via Chinar Test Partner uploaded a Critical Illness policy.	c1bac8c3-1699-41ad-9e82-e3a374ba8974	policy	f	2026-06-17 10:55:31.340709+00
1b5dc1b7-e939-4cb3-b89e-cb21bb7d1975	016370aa-3ed0-4aea-a065-f865aed9e245	policy_uploaded	[Admin] New Policy Upload — POL-2026-249943	Test chinar member (workmytemp@gmail.com) via Chinar Test Partner uploaded a Critical Illness policy.	c1bac8c3-1699-41ad-9e82-e3a374ba8974	policy	f	2026-06-17 10:55:35.758893+00
8ee67ca8-4b5f-4df6-af62-aaba464517c3	c620c95b-ccde-436c-87c6-da3e331ca0bf	policy_uploaded	[Admin] New Policy Upload — POL-2026-249943	Test chinar member (workmytemp@gmail.com) via Chinar Test Partner uploaded a Critical Illness policy.	c1bac8c3-1699-41ad-9e82-e3a374ba8974	policy	t	2026-06-17 10:55:39.569508+00
\.


--
-- Data for Name: otp_log; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.otp_log (id, user_id, email, otp_code, expires_at, is_used, attempts, created_at) FROM stdin;
6559d2dd-6fcd-4e66-8dd9-3f05ace76e50	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$tBMM4rUkFKYBcigY2HQtX.NRoCKzU8MX9U4kNqUytLTMOMuLhxD1S	2026-06-16 13:51:03.544958+00	f	0	2026-06-16 13:41:03.545857+00
df49ed5b-6903-45b3-8a50-224296b270a9	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$B1s0Hex5LODxZtMuQiXlceuL7xwrF7G4e3GkhJaN2mSyY6vw2PAIy	2026-06-16 13:56:05.59169+00	t	1	2026-06-16 13:46:05.592471+00
de7393fe-30f3-43d3-a880-15f00442dd56	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$OnEFjSjqwaqHHouANWVE/uQxuPFzOoL0DNlt4RwqrElQ/xfsdJP6W	2026-06-16 13:56:59.974927+00	t	1	2026-06-16 13:46:59.975705+00
2814d460-2db3-4a9c-8c95-858a1a94afd3	2d42b993-d396-4489-96b4-44baffa94828	partner@healthbridge.in	$2b$12$Msy.pqpv4ebRnkMImd5Jhusv1psXXbxJUbE8tTBQPPlhvwRrgzAHG	2026-06-16 14:08:16.099404+00	t	1	2026-06-16 13:58:16.100128+00
a865aaca-3424-4b50-a1a1-e6980a7e6970	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$do1NCjdDNtSlYCK6qujDj.Hfy1v/azNplfPqeS1WQial7D1z5G02e	2026-06-16 13:46:53.790051+00	t	1	\N
3537c12a-bd5d-4b9d-a21f-9c6e77d8967b	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$EFm8Kqj4WF/Oas/vthUmAOH0UUcUmUQ/DkDQSCdnoc3cqrYqHPMX6	2026-06-16 13:57:47.304384+00	t	1	2026-06-16 13:47:47.305222+00
27faa38b-c78a-45af-af77-a402d865ec8d	2d42b993-d396-4489-96b4-44baffa94828	partner@healthbridge.in	$2b$12$QMaXwLam./jWWfHiQfs4beo9Mro3mWkQDvAI7eJlWb4fu0DOdW3o6	2026-06-16 13:47:28.10923+00	t	1	\N
f5cb0c70-9493-4c7c-8de0-e0d907035184	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$ogBU3VmttSMFbaGG6un1eeXRbr4XYyEiDq65Y.1wai5vkr1LBQjFW	2026-06-16 14:02:07.477911+00	t	1	2026-06-16 13:52:07.479751+00
5c1d3cc3-4d3c-46fd-9d04-ef727567ee8f	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$ACb/N/AWHn0SNmby4IJ.zem4mePXiF1TrpJwBhoOwbdGjxZfnJIQa	2026-06-16 13:55:29.950452+00	f	2	2026-06-16 13:45:29.952405+00
f506939c-5c9b-4af7-bb44-88acf9c10e2d	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$/MbNPCqWuRVH./AY9VJ9NevUyNNLznZ4Yu9IOO2Qr3CpB6ZXRnCj.	2026-06-16 14:03:01.770335+00	t	1	2026-06-16 13:53:01.771365+00
87b7f4f0-6099-4fc9-9bde-c083484d8d70	c0b50711-22bf-4ea6-a7d7-f932591705fb	rahul@example.com	$2b$12$mhkSkU7Iyj1s1H7iKHwAROhbf1iz4QtNJYlLzoAHzmT9Z5raigBv2	2026-06-16 13:47:49.756397+00	t	1	\N
6687e7a0-e607-4734-b96b-9dbf0f8a32c7	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$zOdR0mpUHXBAosmXDVF1eOhNJprLy7MakBhXyudGNo3gdmcJ2cP0y	2026-06-16 14:06:15.340993+00	t	1	2026-06-16 13:56:15.341703+00
84a9ae27-e8d9-4410-ba7f-8ee4d75acf51	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$KZgG11h.ql3wKZPJ0LVsZ.b1LlvyLVBG2o4s6cpPtkMWVHsO8xsJG	2026-06-16 13:48:54.849682+00	f	0	2026-06-16 13:38:54.850398+00
d5e2afd1-a997-4917-91f7-cec61b891d35	016370aa-3ed0-4aea-a065-f865aed9e245	admin@easyclaims.in	$2b$12$L6qiV3W7CXnekxnM7ro04O/zVI4MEXv6PAKXeCukpRRcmYRw0xXj.	2026-06-16 12:52:47.157934+00	t	1	\N
5f2d338c-48a5-4ba4-9b3b-a93886ebb6a9	016370aa-3ed0-4aea-a065-f865aed9e245	admin@easyclaims.in	$2b$12$2cb1IwZMLKLBqnIjAhXHqOM2/CjuZho0lR3WZQvkD22p7ZdXorF7m	2026-06-16 12:53:43.066852+00	t	1	\N
4868fe2a-4153-48c3-afa6-b4717384971f	016370aa-3ed0-4aea-a065-f865aed9e245	admin@easyclaims.in	$2b$12$3Kem2NBGC88RZlD1hETmG.RyqWy1z6yWH0WtQLN3aPCYab7AwIiBK	2026-06-16 12:57:28.037258+00	t	1	\N
1ff7c9e3-2eb1-496b-b3cf-6d3b57b05000	016370aa-3ed0-4aea-a065-f865aed9e245	admin@easyclaims.in	$2b$12$8DCaUNdvxxNN3iPdBoxVo.yy7pOB.s2sD2.5fCvay0vsNvdFfUqqq	2026-06-16 12:58:25.053224+00	t	1	\N
3c5d8a47-df9a-4911-8840-fd067ee17c17	b5569ec9-1a95-4969-9a97-a714e82c5ba7	partner_1781614104@test.com	$2b$12$FqMUakSQ1FWHNa8siO9CwewXjXQei5eZSWQffNNlo3XlgvobXNnwG	2026-06-16 12:58:25.72787+00	t	1	\N
6ae53777-2fd4-426a-8a34-30aca0e1006a	016370aa-3ed0-4aea-a065-f865aed9e245	admin@easyclaims.in	$2b$12$akLLsA6a8Dx0BD7MMuZA.uhB3sV7VpPne.m.pydVPXZi4gRHHSrGC	2026-06-16 12:59:02.595779+00	t	1	\N
167b2ecb-68ae-43a5-8d0b-40ac14e228f6	016370aa-3ed0-4aea-a065-f865aed9e245	admin@easyclaims.in	$2b$12$o9Li/90zquAXDcLpA5adCuJgQLiIS9noCfh5UpsW7qCvZSH3Dz/a.	2026-06-16 12:59:53.796932+00	t	1	\N
8f627ed4-9b35-47c7-8f84-083391a168d5	016370aa-3ed0-4aea-a065-f865aed9e245	admin@easyclaims.in	$2b$12$/tziXFaKH9GzKGPqhyHLmOlvAg9Q0SY8OuWkbNFojJ9NLDQnQR6a.	2026-06-16 13:00:54.042824+00	t	1	\N
8afcc6d7-131d-40b8-9404-f11c8d9b0b11	b677f283-5b8d-42ae-bcb0-0af5808697c3	partner_342a5630@test.com	$2b$12$erUSZhvCC43ksb2CecA4tehXeeiobcqb6EGjKN9VbGiMpBOUqWyQS	2026-06-16 13:00:54.683955+00	t	1	\N
dd36dd81-83e9-467f-ae72-c69984623b15	3f663e54-b4bb-4fa7-abf3-1b632a9f7893	member_342a5630@test.com	$2b$12$2ofsHzk8mcz4Z0x4kqkN.OuMdZ3Twq2Zvd8Mvaze/mxWFaM9TL..a	2026-06-16 13:00:58.543118+00	t	1	\N
fe39b8a8-e9b7-404e-88b8-c7844dfe27d6	016370aa-3ed0-4aea-a065-f865aed9e245	admin@easyclaims.in	$2b$12$s3UEZTTonl6WhuVENralcu7sRh/onUUgarXmocoaAAeCVfeg2IGxS	2026-06-16 13:03:37.634008+00	t	1	\N
60dd1f5c-7245-4d87-8176-d077c20d16a0	016370aa-3ed0-4aea-a065-f865aed9e245	admin@easyclaims.in	$2b$12$B.hLziokggeouBPNrVtgWOAIQytJtdz8iKPEtHIjSGFvT6QzcJXGa	2026-06-16 13:39:26.854208+00	f	0	2026-06-16 13:29:26.855941+00
55f18cfb-a254-4f33-8638-f5c51d2bd89d	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$D6BFhO288L1HEWvGDOz0ierwsuIIMoMNk4nw08fZjhn/oBwbBO0vO	2026-06-16 14:07:10.622385+00	t	1	2026-06-16 13:57:10.623169+00
689449da-2d0e-4e2f-983f-90e3d564ff6d	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$Ju7nLremGr2JN6OL3nTRmuarjnR7L/khw1FcGUM8k25AZqtYqUhPm	2026-06-16 14:07:26.289513+00	t	1	2026-06-16 13:57:26.290479+00
d2ba689b-25f0-4af6-9e3a-e411dec9f38e	2d42b993-d396-4489-96b4-44baffa94828	partner@healthbridge.in	$2b$12$8wFLqLUUyvsLYLvgj67y..zPq23xO6gMrRyBd2ahrFoKL5UDjzPgO	2026-06-16 14:07:47.085448+00	t	1	2026-06-16 13:57:47.086309+00
43195dc1-0aa3-4afa-9ac4-ef89b6795a79	c0b50711-22bf-4ea6-a7d7-f932591705fb	rahul@example.com	$2b$12$Ghl2cWfHlmQybCn9hbrLi./oMevLpPGVFHFPrtMCf2WpfXZXGxiYq	2026-06-16 14:07:50.253629+00	t	1	2026-06-16 13:57:50.254369+00
41b9801e-7d61-4fb7-9aa1-2f4f24764a93	2d42b993-d396-4489-96b4-44baffa94828	partner@healthbridge.in	$2b$12$em5daN3/MxG3uOVkTXL6w.ubJiKCgvXZib3Ju6H3XMX4WQ2R3Ho0m	2026-06-16 14:08:02.701102+00	t	1	2026-06-16 13:58:02.702115+00
1f07b440-fd0d-4623-b9f0-73b7513fb544	c0b50711-22bf-4ea6-a7d7-f932591705fb	rahul@example.com	$2b$12$L3vn/mQvZgoYCVtNpQ5u5eUSQlq3s1iRwnIP852gMg.kv.OnjskN.	2026-06-16 14:08:59.868486+00	t	1	2026-06-16 13:58:59.869189+00
2dba1a8a-6dac-4cc3-9a43-584f4bf90841	c0b50711-22bf-4ea6-a7d7-f932591705fb	rahul@example.com	$2b$12$GkS4Rt3M08jTtqNoWZ376uVmZryTejeirYfh/cisNWdaHZYDB/74.	2026-06-16 14:11:27.619737+00	t	1	2026-06-16 14:01:27.620454+00
3ebb9b4c-e0c5-4cd2-8852-8bf7b40fb198	c0b50711-22bf-4ea6-a7d7-f932591705fb	rahul@example.com	$2b$12$bowY3zSzWdpHXb81.QTchu3vaivPxG9q.Y1LuytEz85HXOKI9Q6Ee	2026-06-16 14:11:45.922256+00	t	1	2026-06-16 14:01:45.923142+00
1c1d643c-2be0-4006-a5a9-0ada8cba6ecc	c0b50711-22bf-4ea6-a7d7-f932591705fb	rahul@example.com	$2b$12$kjMkM8BANiKKT4FQII2gZuL6/uCrPCGt5k.HyfMNceQt9wry0LlZO	2026-06-16 14:12:03.012755+00	t	1	2026-06-16 14:02:03.013668+00
0a831fee-424e-4a75-8b22-d66672d1ce62	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$ddFqmkSMmzMazc/Ai1XFNuqhSOOJ0Tc29aBLyABz1XVhNifA1BF.C	2026-06-16 14:14:05.47107+00	t	1	2026-06-16 14:04:05.471923+00
f0490cdc-117c-483d-a4a7-43e7ccd9e929	c0b50711-22bf-4ea6-a7d7-f932591705fb	rahul@example.com	$2b$12$DD/o.I9e/pS5gnxl2Vvy/O.Ismp8WeWXkXCu5/8fMG8aYxJaGcb1G	2026-06-16 14:14:09.333949+00	t	1	2026-06-16 14:04:09.334713+00
c92e7d52-5806-41da-b9dc-f0efa324fa84	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$11YksZqb4I6Kc5oyT/op4ugpif/HfFi2ybEZYQ.7UrL/vrJUizzjC	2026-06-16 14:15:36.631322+00	f	0	2026-06-16 14:05:36.632026+00
07bde9b7-2094-4a83-97cc-2bf7a2eb3c43	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$cKagdDIGwC85s8uVgqTovuQCsPY.cm.h6dELGaHO2JZwDEq98Btme	2026-06-16 14:17:53.503185+00	t	1	2026-06-16 14:07:53.504047+00
ae46d90d-ed9a-41b7-9da5-4c704b198e1a	c0b50711-22bf-4ea6-a7d7-f932591705fb	rahul@example.com	$2b$12$4bK1bEHPZmJ6CzbZbK7CH.yagsZOdPS0d5/4Ac4vBoYfgSByMFIwi	2026-06-16 14:17:56.897893+00	t	1	2026-06-16 14:07:56.898674+00
d9874be4-6555-4e65-b81c-59ac357a9572	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$XT8gkC8VkxhUV.Dg6Hc4UuMKLQfZW4L0Zs97CP6576ewezw0564dK	2026-06-16 14:20:36.632565+00	t	1	2026-06-16 14:10:36.633281+00
07499f38-dccd-4d8a-8cfc-05547cea6bb9	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$/eNo5YF7rsmwF6LhATYQ1.NOW2TcmjQ/e8HFnhwM9bSL2vOcslFi6	2026-06-16 14:20:46.215459+00	t	1	2026-06-16 14:10:46.216249+00
e0778c93-74d7-4ea7-9b74-e20e0e7f63db	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$FlDQj9rGPZTLURZAtvoP1.5ZULzLjYgL9iCglqiDir/F3/4sHoq2q	2026-06-16 14:20:57.903864+00	t	1	2026-06-16 14:10:57.904585+00
62b09a4e-362b-4d2a-8ccf-1d1a2d1d71cc	2d42b993-d396-4489-96b4-44baffa94828	partner@healthbridge.in	$2b$12$pxzlE4ci7W4pFM2ySaO5Z.E9H4vO9etiSnX9eOJaZMteEcZPPMkEy	2026-06-16 14:21:47.668408+00	t	1	2026-06-16 14:11:47.669243+00
b84c0175-e0bb-4e6b-ba60-599516bfdb2d	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$enbi7IcrsLoeVRDxSi4aOO8TSVqzIIiw2cCe5bVB1VegnmzZ6Tl52	2026-06-16 14:22:33.272917+00	t	1	2026-06-16 14:12:33.273692+00
17d26ff8-e543-421d-b920-b69eab44139e	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$CBpKGURs/Q8hJC6jmbrQ5.XnMQLkfzZX1kH/s0Y6aVKrQoRerY1F6	2026-06-16 14:23:30.542295+00	t	1	2026-06-16 14:13:30.543199+00
0e03da27-c420-43dc-a032-296bec9768af	cd32eb60-940a-4016-8a3d-1b3d251e3d27	chinarvartak@gmail.com	$2b$12$vFcl4zMHiM3t18uFjrUHNuLP.3dxKuvZFamt1YrlLw/31h8MI.tqC	2026-06-16 14:24:57.931895+00	t	1	2026-06-16 14:14:57.932751+00
f83861e3-cf43-40ba-9720-f0e21f2f3bd3	83f2ce28-c466-4687-98f1-24ab2340d531	chinarartak@gmail.com	$2b$12$GCYgsPK.VbuW3kqbQ4z4x.EU/zeZSs.cp5lx7AtEqODDmQl2jqBvC	2026-06-16 14:26:19.171787+00	t	1	2026-06-16 14:16:19.172626+00
386cb3ce-dac4-4077-8754-48e19c2f9d8c	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$mHphU1b2DQP5AOD.UNNa.uk2lDcN/w.Ip3nKxm5SGyTeriz.CYFfG	2026-06-16 14:40:40.94375+00	t	1	2026-06-16 14:30:40.944686+00
1d34055f-592f-481d-9ea1-445f5a0b28f2	c0b50711-22bf-4ea6-a7d7-f932591705fb	rahul@example.com	$2b$12$1zhUETjkM/HTKUeUJ4vMcewDpZUkMcUFdV0HWLXwW1aAT238Thepm	2026-06-16 14:58:30.737171+00	t	1	2026-06-16 14:48:30.738579+00
da18195e-de55-46ae-9401-492492b3c649	cd32eb60-940a-4016-8a3d-1b3d251e3d27	chinarvartak@gmail.com	$2b$12$mxVZOH9o1iJQvMFrdL.8Ke3MDJoWmU/r3hWrNeTncIbFRw7yHXYX6	2026-06-16 15:07:46.372282+00	t	1	2026-06-16 14:57:46.373241+00
c4c89a44-fa17-40b1-af1d-32b850d0d37d	83f2ce28-c466-4687-98f1-24ab2340d531	chinarartak@gmail.com	$2b$12$UZP65IyUrJxmo2DlxsiKi./56MbouRmZa1a3KmPykQcDG64gKHyr.	2026-06-16 15:08:51.66501+00	t	1	2026-06-16 14:58:51.666007+00
040263b8-083e-462f-b2ec-85dde95276c2	cd32eb60-940a-4016-8a3d-1b3d251e3d27	chinarvartak@gmail.com	$2b$12$E9N7HtAu02iPeu.5ZgsXEOrxHmStabj0TWPVSvyfIYy.V0S4wmeUK	2026-06-16 15:14:55.983818+00	t	1	2026-06-16 15:04:55.984728+00
c307281f-8eac-4040-8d3c-7bd32fc34b5d	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$GcAAok3mW2pLsH31ihc0yenUOJOntGpu2zv9clSgtHORnYl3032cC	2026-06-16 15:36:28.978216+00	t	1	2026-06-16 15:26:28.979575+00
0f1828c2-b878-49f0-8f0c-9f1025431846	83f2ce28-c466-4687-98f1-24ab2340d531	chinarartak@gmail.com	$2b$12$3dxb.OjT.krtTwFuI4TYrOv1Jkj9leU8nbjHyICnulwdv82GsFJp2	2026-06-16 15:37:22.99987+00	t	1	2026-06-16 15:27:23.000723+00
8063bd63-949b-422f-85cc-a8c010ad0e6c	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$uR87N31tjB32XIP0pyyjB.dLKjfcCCb2SLiFGWN266E.kA6EeljH6	2026-06-16 15:46:26.093442+00	t	1	2026-06-16 15:36:26.094202+00
f0c78e7b-3762-4658-88a8-96518b3958e2	4444a2f9-ad30-4414-8491-f4025b6f76ba	chinar.vartak@gmail.com	$2b$12$1qwNBZgecWgSRljqmDJQhOToyziJGQYrV7arsccJFssv94kzPq6tu	2026-06-16 15:58:17.798181+00	t	1	2026-06-16 15:48:17.799178+00
69f4b663-cffd-476b-bea7-15371d75f4db	cd32eb60-940a-4016-8a3d-1b3d251e3d27	chinarvartak@gmail.com	$2b$12$6Ucza92EsuPQZ.tgOZg6RuwD5qmjiOlqJ7yXQzoX.G.YnFkAzq1qG	2026-06-16 15:58:44.567614+00	t	1	2026-06-16 15:48:44.568422+00
7d757d9d-2e39-4a8c-92ec-2366d1417fae	4444a2f9-ad30-4414-8491-f4025b6f76ba	chinar.vartak@gmail.com	$2b$12$TqlCLJEno8pAd3v1TKUTVOYVu/Eh8eOmah1ptewosGuVotAIVIkye	2026-06-16 15:59:00.669122+00	t	1	2026-06-16 15:49:00.669892+00
e03b8e16-76a4-4331-8b52-af4aa336468f	cd32eb60-940a-4016-8a3d-1b3d251e3d27	chinarvartak@gmail.com	$2b$12$f0350pA53wfxL2ECYt1QoOPqpLDoNc7os4dV4E/Y1OfpzuUnYgYqC	2026-06-16 15:59:26.538238+00	t	1	2026-06-16 15:49:26.539156+00
a9ecc95c-f809-44f1-b5c1-a0cea530712a	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$cETiOi90j5D.paUqnrfM9.erAEg.jsu5l7rJCBr5.bzNHRMYFRItq	2026-06-16 15:59:40.802401+00	t	1	2026-06-16 15:49:40.803152+00
9e1f1ce3-6f3b-4bbb-a0aa-c3d4289500fc	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$jWcWFTYwEZQf5AVeulEfCu0FbfxLN39jKZJEMn0g6hCsJkKCBXspS	2026-06-16 16:50:38.277304+00	t	1	2026-06-16 16:40:38.280253+00
a92d8180-275e-42ae-91c5-8412de1ea0b1	cd32eb60-940a-4016-8a3d-1b3d251e3d27	chinarvartak@gmail.com	$2b$12$udTxjL.4YGEcBETr1JwQlOdpdU8joGzrKFx8TRAzDHmgkcrWKvcpS	2026-06-16 16:51:51.864552+00	t	1	2026-06-16 16:41:51.86528+00
88a4f7d8-3128-4fdb-8346-0bcead1c3ab1	83f2ce28-c466-4687-98f1-24ab2340d531	chinarartak@gmail.com	$2b$12$rs25Uu5YIyn5Yr4zIco2AutKPeC5YT590TBTMNPg3wkN7Vs.uIgK6	2026-06-16 16:52:46.314969+00	t	1	2026-06-16 16:42:46.315928+00
92c54c8c-10bd-4242-9766-3ac7cc6ce33a	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$3QHvMfIPpfcf1Q9KngjZXOFSb2fSgIEwvA1.fw5z/EPaBjsqW9fVK	2026-06-17 07:05:32.954004+00	t	1	2026-06-17 06:55:32.954881+00
7a5cf464-1218-4ddf-b8e2-e9913f44da97	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$1mQW62ZYyDxYEUUrUXBto..AjUoxA4g2Di0/Lb4wzeTOyKeMBYIT6	2026-06-17 07:31:28.716348+00	t	1	2026-06-17 07:21:28.718138+00
3fc49e2d-f6f9-4add-a695-d5f66123a31d	213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	$2b$12$md3ww5yRJ6SQ5dmxPtszg.Rd/HkVa9KZFYuqBLXMQdka4FZGHOBPG	2026-06-17 09:37:14.172418+00	f	0	2026-06-17 09:27:14.174218+00
36a1b9ba-8329-4222-9d9c-845c58cd0dcd	c620c95b-ccde-436c-87c6-da3e331ca0bf	chinarvartak6@gmail.com	$2b$12$Ke7Tgops8RgGWx6IgH.Xgu1/K6WYfutMRJ5nVVdRcLR3ydPFaQAH.	2026-06-17 09:38:09.56249+00	f	0	2026-06-17 09:28:09.563265+00
ff950ada-86f0-412a-a5c2-97c43c63a57d	c620c95b-ccde-436c-87c6-da3e331ca0bf	chinarvartak6@gmail.com	$2b$12$4mExq/ARAnJrH.2xH5Hrp.NI6.YY3ZkZj6lajHbrpzQAqP7ZvZmcO	2026-06-17 09:39:07.589945+00	t	1	2026-06-17 09:29:07.590798+00
e0f08b72-26bd-4cb7-a514-51ff409da054	cd32eb60-940a-4016-8a3d-1b3d251e3d27	chinarvartak@gmail.com	$2b$12$owfHJd.umuC0BsXpzkDl1OVQfE47jkH8oFW1kzntdZLcyY4HKfJ52	2026-06-17 09:46:26.272684+00	t	1	2026-06-17 09:36:26.273532+00
4541a991-8ddb-430e-bb6f-5221cd78ac3f	38eb24db-e6e4-4ade-8c8d-ac9942c6d9eb	workmytemp@gmail.com	$2b$12$6gjokQXW82.QLEUnRxgq3OTBfftrozEweGBzQRKK8vrGUOmN0P/42	2026-06-17 09:49:50.472804+00	t	1	2026-06-17 09:39:50.47369+00
956b0517-971a-4974-b994-c7fe638ccdcb	c620c95b-ccde-436c-87c6-da3e331ca0bf	chinarvartak6@gmail.com	$2b$12$5.P6UqQtPf/0s9zxgnfVpesuIge0r/hQbPNLaDQU0BgrOH3FAp1pi	2026-06-17 09:51:02.40897+00	t	1	2026-06-17 09:41:02.409763+00
fec5c8b8-0cd4-4815-8bbe-af788ffff242	4444a2f9-ad30-4414-8491-f4025b6f76ba	chinar.vartak@gmail.com	$2b$12$2oFcU2KdhImjWbLrV9RyyuMEV3fvSmx.3f2YqHG4qFNxQdiM7e4wy	2026-06-17 09:55:20.967801+00	t	1	2026-06-17 09:45:20.968635+00
b3ab8f7c-1baf-416c-9596-35fc011b5a5c	cd32eb60-940a-4016-8a3d-1b3d251e3d27	chinarvartak@gmail.com	$2b$12$av/us5bFEcSebOMokv9m5OiKopxYqo4e4YCTWw.FQER8kgEDnL/MC	2026-06-17 10:27:40.65949+00	f	0	2026-06-17 10:17:40.661339+00
2d9f8d52-c528-4edb-89c2-5a692044073b	c620c95b-ccde-436c-87c6-da3e331ca0bf	chinarvartak6@gmail.com	$2b$12$av4bTbbKGQSxXvvpRs390OE79RMgdlNRnxr6QLtOieVbZZzpjFZJS	2026-06-17 10:27:53.325522+00	t	1	2026-06-17 10:17:53.326686+00
15099a4d-fe78-4f39-9600-67c1fa5cfe3b	4444a2f9-ad30-4414-8491-f4025b6f76ba	chinar.vartak@gmail.com	$2b$12$WZ3uOoWozeOt91Zl2ntS0esorsE9tMxx5TUaDh0rgb7d5hgQcih.6	2026-06-17 10:36:06.398003+00	t	1	2026-06-17 10:26:06.399722+00
a94082ee-f22a-497a-a4d4-378732a49b48	38eb24db-e6e4-4ade-8c8d-ac9942c6d9eb	workmytemp@gmail.com	$2b$12$r40iH.Q9yg06LiBaHtClpO1AkeuXjc7fb9s5fjrUUjb0QC2qRRH8W	2026-06-17 10:37:50.371135+00	t	1	2026-06-17 10:27:50.371984+00
8bd86daf-4b36-4f6d-b64c-f6274ec8e522	c620c95b-ccde-436c-87c6-da3e331ca0bf	chinarvartak6@gmail.com	$2b$12$kHOMDKqVRAUeKPiDSGr8fO0ABNF8OjDu.HODkXAag3ljnjY2MxB7.	2026-06-17 11:56:12.284459+00	t	1	2026-06-17 11:46:12.287181+00
5602f769-3d2d-494d-8f6b-beea0091ed23	cd32eb60-940a-4016-8a3d-1b3d251e3d27	chinarvartak@gmail.com	$2b$12$iVZ.mf7t1uBnPOc8VkzppOOTzDk4ayM3L1z68Fj9M716T2S.2edIG	2026-06-17 12:06:08.540642+00	t	1	2026-06-17 11:56:08.541419+00
76e547ef-4a06-41bb-99ab-aeab6a3d6c26	38eb24db-e6e4-4ade-8c8d-ac9942c6d9eb	workmytemp@gmail.com	$2b$12$vW9pngsouRRkJI9btUUKcOT3mMtmBJbE.sYmk9yY1T2YUhkBvxREa	2026-06-17 12:12:32.394194+00	t	1	2026-06-17 12:02:32.39492+00
5dd014b8-93fe-44b3-8304-da7c43cdf9b4	cd32eb60-940a-4016-8a3d-1b3d251e3d27	chinarvartak@gmail.com	$2b$12$n6TALQzq8QgpbKYg8Acwm.IGfeyHL5RO/g21s8EYDG7yVq3BJFEh2	2026-06-17 12:40:12.985925+00	f	0	2026-06-17 12:30:12.988012+00
411e290e-4f03-431c-8a2d-64b9afd14699	38eb24db-e6e4-4ade-8c8d-ac9942c6d9eb	workmytemp@gmail.com	$2b$12$oP.BFRGrhq9OxZNb/OkbMeadtlLAV1j/rj4SxoJ.bsV30QEZgaa86	2026-06-17 12:40:37.613553+00	t	1	2026-06-17 12:30:37.61449+00
3b76c075-fc88-4d38-825e-427686cd35aa	c620c95b-ccde-436c-87c6-da3e331ca0bf	chinarvartak6@gmail.com	$2b$12$QX7sTYu2wwkKEhdmN0eYX.AfVXsG7m064kfyBgRRbS/D/gVtgd0YC	2026-06-17 13:06:29.557719+00	t	1	2026-06-17 12:56:29.558564+00
b1a95e90-a410-4df8-9b6c-67d3a8a90c05	38eb24db-e6e4-4ade-8c8d-ac9942c6d9eb	workmytemp@gmail.com	$2b$12$FrW6k2JMV63NV0djXFPIJ.MnHZrUnSUm6FbIq5Db3fi7i32eelMCm	2026-06-17 13:10:23.811534+00	t	1	2026-06-17 13:00:23.812346+00
bc8bc846-7830-4117-b32a-525ebf6c353e	c620c95b-ccde-436c-87c6-da3e331ca0bf	chinarvartak6@gmail.com	$2b$12$BcdHszp8EH.h0vIANmwDWOthpvL88k4SqkC79VcrsTpw.o1IlCv/i	2026-06-17 13:20:41.058786+00	t	1	2026-06-17 13:10:41.059627+00
5c78f3be-3c71-4e93-8289-fa20b4050436	cd32eb60-940a-4016-8a3d-1b3d251e3d27	chinarvartak@gmail.com	$2b$12$3mWO6STIi2aKLMGAUeZOHeeP8czTSblXm.WUMWXJTwyMeTopGqL0y	2026-06-17 13:21:47.707317+00	t	1	2026-06-17 13:11:47.70803+00
0c27fbee-611f-47df-b69f-e4d9044f84f8	c620c95b-ccde-436c-87c6-da3e331ca0bf	chinarvartak6@gmail.com	$2b$12$T4CyHYRlE2GiydJTLmCoQu9B6DSM4mUMmgHl9VOgY9kYfO39WKi6m	2026-06-17 18:28:45.125938+00	t	1	2026-06-17 18:18:45.126846+00
\.


--
-- Data for Name: partner_plans; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.partner_plans (id, partner_id, plan_id, created_at) FROM stdin;
8e0748c8-a7ad-4c39-9248-95516578217a	f25c2437-b295-4017-af89-83c477c10185	82fee7bc-1f99-4132-bd31-718e1a661a37	2026-06-16 15:47:43.01478+00
a803bfa3-95c0-431b-a26f-c7e272e0ab54	c93adfb1-c37a-4db3-8426-6e24c30101bf	82fee7bc-1f99-4132-bd31-718e1a661a37	2026-06-16 15:47:43.025371+00
bbbef605-8801-4ee4-a365-5f3d28cad948	00dfeec1-f697-413a-93ed-f437a9cf9a53	8c39e9b5-5491-43f5-a0a4-0415d275f2e6	2026-06-17 07:22:02.508635+00
d55f6017-ed8c-4277-bf28-dad12c782ac5	f25c2437-b295-4017-af89-83c477c10185	8c39e9b5-5491-43f5-a0a4-0415d275f2e6	2026-06-17 09:44:00.714833+00
d3cd2d92-b767-4693-bf01-78ddfe60f106	c93adfb1-c37a-4db3-8426-6e24c30101bf	8c39e9b5-5491-43f5-a0a4-0415d275f2e6	2026-06-17 09:44:00.720149+00
\.


--
-- Data for Name: partners; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.partners (id, user_id, name, partner_type, city, status, api_key, api_rate_limit, is_deleted, created_at, updated_at) FROM stdin;
f867d0d4-21dc-4219-acfe-32d022addd05	b5569ec9-1a95-4969-9a97-a714e82c5ba7	Test Brokers Ltd	Broker	Mumbai	Active	366210d534554915be4998b86c4a81c1	600	f	2026-06-16 12:48:25.440602+00	2026-06-16 12:48:25.440606+00
00dfeec1-f697-413a-93ed-f437a9cf9a53	b677f283-5b8d-42ae-bcb0-0af5808697c3	Test Brokers Ltd 342a5630	Broker	Mumbai	Active	911291f0d8294308a30ad2ad5e9e925b	600	f	2026-06-16 12:50:54.396876+00	2026-06-16 12:51:18.984726+00
6cd47d22-9412-46e5-ad7a-3a274d141f29	2d42b993-d396-4489-96b4-44baffa94828	HealthBridge Brokers	Broker	Mumbai	Active	b9af294129c841ca93bcc39db923c1f2	600	f	2026-06-16 11:18:24.257859+00	2026-06-16 15:48:04.738615+00
f25c2437-b295-4017-af89-83c477c10185	cd32eb60-940a-4016-8a3d-1b3d251e3d27	Chinar Test Partner	Broker	vasai	Active	abd311cab19b478ab440c5939b063182	600	f	2026-06-16 14:14:46.03257+00	2026-06-17 09:36:03.562313+00
c93adfb1-c37a-4db3-8426-6e24c30101bf	4444a2f9-ad30-4414-8491-f4025b6f76ba	chinar Test Partner 2	Broker	vasai	Active	78e8865c920f4f2aacc00075fc6cd11c	600	f	2026-06-16 13:54:36.536511+00	2026-06-17 09:42:33.830198+00
\.


--
-- Data for Name: policies; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.policies (id, user_id, partner_id, policy_number, insurer, sum_insured, start_date, end_date, status, ai_confidence, extracted_fields, is_deleted, created_at, updated_at, policy_type_id, storage_key, file_name) FROM stdin;
a4a1812e-a5d8-4629-9b16-004ac2bad002	c0b50711-22bf-4ea6-a7d7-f932591705fb	6cd47d22-9412-46e5-ad7a-3a274d141f29	POL-2026-712498	Star Health	500000	\N	\N	pending	\N	{}	f	2026-06-16 11:47:51.729379+00	2026-06-16 11:47:51.729382+00	6e0c4c8f-a7c7-44a1-b9f2-d9f8fa2ad8ae	uploads/policies/c0b50711-22bf-4ea6-a7d7-f932591705fb/e9a6e084-db6d-43d4-a85f-1fd6a23b0d11.pdf	e9a6e084-db6d-43d4-a85f-1fd6a23b0d11.pdf
943eea11-a31e-470e-bf98-0e2081478524	c0b50711-22bf-4ea6-a7d7-f932591705fb	6cd47d22-9412-46e5-ad7a-3a274d141f29	POL-2026-238296	Star Health	1000000	\N	\N	pending	\N	{}	f	2026-06-16 11:55:04.597588+00	2026-06-16 11:55:04.597591+00	6e0c4c8f-a7c7-44a1-b9f2-d9f8fa2ad8ae	6cd47d22-9412-46e5-ad7a-3a274d141f29/c0b50711-22bf-4ea6-a7d7-f932591705fb/943eea11-a31e-470e-bf98-0e2081478524/ce58d319-e00e-44b8-a94a-0181bc7ef8b4.pdf	ce58d319-e00e-44b8-a94a-0181bc7ef8b4.pdf
7702e8f8-5067-4335-b821-d11dcaf6a23e	3f663e54-b4bb-4fa7-abf3-1b632a9f7893	00dfeec1-f697-413a-93ed-f437a9cf9a53	POL-2026-189101	Star Health Insurance	1000000	\N	\N	pending	\N	{}	f	2026-06-16 12:50:58.973872+00	2026-06-16 12:50:58.973877+00	6e0c4c8f-a7c7-44a1-b9f2-d9f8fa2ad8ae	00dfeec1-f697-413a-93ed-f437a9cf9a53/3f663e54-b4bb-4fa7-abf3-1b632a9f7893/7702e8f8-5067-4335-b821-d11dcaf6a23e/d186af04-e0a7-4abc-bed5-6b5a304bd430.pdf	d186af04-e0a7-4abc-bed5-6b5a304bd430.pdf
09fbc4a0-471b-4f1d-b8d6-599fe5f4ec03	3f663e54-b4bb-4fa7-abf3-1b632a9f7893	00dfeec1-f697-413a-93ed-f437a9cf9a53	POL-2026-285982	HDFC ERGO	500000	\N	\N	pending	\N	{}	f	2026-06-16 12:51:08.949771+00	2026-06-16 12:51:08.949774+00	ef31fd4a-1e92-425b-b94b-636dff3e8f08	00dfeec1-f697-413a-93ed-f437a9cf9a53/3f663e54-b4bb-4fa7-abf3-1b632a9f7893/09fbc4a0-471b-4f1d-b8d6-599fe5f4ec03/3795fc98-4ebc-4fbc-b05a-28094620b175.pdf	3795fc98-4ebc-4fbc-b05a-28094620b175.pdf
9dac6be6-b763-4692-9cf9-92e848d895cb	83f2ce28-c466-4687-98f1-24ab2340d531	f25c2437-b295-4017-af89-83c477c10185	POL-2026-111461	dsds	10000	\N	\N	pending	\N	{}	f	2026-06-16 15:28:12.015061+00	2026-06-16 15:28:12.015071+00	6e0c4c8f-a7c7-44a1-b9f2-d9f8fa2ad8ae	f25c2437-b295-4017-af89-83c477c10185/83f2ce28-c466-4687-98f1-24ab2340d531/9dac6be6-b763-4692-9cf9-92e848d895cb/a7112770-2816-4074-a491-95f7fd54c5bb.pdf	a7112770-2816-4074-a491-95f7fd54c5bb.pdf
c1bac8c3-1699-41ad-9e82-e3a374ba8974	38eb24db-e6e4-4ade-8c8d-ac9942c6d9eb	f25c2437-b295-4017-af89-83c477c10185	POL-2026-249943	HDFC	1000000	\N	\N	pending	\N	{}	f	2026-06-17 10:55:17.619724+00	2026-06-17 10:55:17.619728+00	21663803-bfeb-4e29-87b5-89b1fc98c05e	f25c2437-b295-4017-af89-83c477c10185/38eb24db-e6e4-4ade-8c8d-ac9942c6d9eb/c1bac8c3-1699-41ad-9e82-e3a374ba8974/5215f07d-198c-4e4c-9bee-790dbc929549.pdf	5215f07d-198c-4e4c-9bee-790dbc929549.pdf
\.


--
-- Data for Name: policy_family_members; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.policy_family_members (id, policy_id, family_member_id, created_at) FROM stdin;
aa21ba6e-0643-4182-a581-140f5883719b	7702e8f8-5067-4335-b821-d11dcaf6a23e	c7e82460-fdad-412d-97e8-6611dec4f5b0	2026-06-16 12:51:08.933271+00
d7b84049-1287-4166-9954-ea825a535fa7	9dac6be6-b763-4692-9cf9-92e848d895cb	19dcca3c-abcc-4474-823f-a0cbdf96ca4c	2026-06-16 15:28:21.595601+00
550010da-b92f-4704-bd4a-96d00b641988	c1bac8c3-1699-41ad-9e82-e3a374ba8974	b9846833-1575-41a1-8efd-0cb9f81accac	2026-06-17 12:04:18.84764+00
07ab19f4-f4c4-4c2e-aa9f-728eb732f6d3	c1bac8c3-1699-41ad-9e82-e3a374ba8974	10fb7608-47b1-4bb3-b0aa-2d7800127ce7	2026-06-17 12:04:18.862821+00
\.


--
-- Data for Name: policy_types; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.policy_types (id, name, code, description, is_active, created_at, updated_at) FROM stdin;
6e0c4c8f-a7c7-44a1-b9f2-d9f8fa2ad8ae	Health	health	Medical health insurance	t	2026-06-16 11:53:28.564033+00	2026-06-16 11:53:28.564033+00
35c5cb11-6560-4c92-83a2-8456b610ed25	Life	life	Life insurance	t	2026-06-16 11:53:28.564033+00	2026-06-16 11:53:28.564033+00
31b76f63-4e43-415f-b89c-61db36b09fd4	Term	term	Term life insurance	t	2026-06-16 11:53:28.564033+00	2026-06-16 11:53:28.564033+00
ef31fd4a-1e92-425b-b94b-636dff3e8f08	Motor	motor	Vehicle insurance	t	2026-06-16 11:53:28.564033+00	2026-06-16 11:53:28.564033+00
e7a749f9-5cbc-45fe-81de-ce4910a5ed84	Travel	travel	Travel insurance	t	2026-06-16 11:53:28.564033+00	2026-06-16 11:53:28.564033+00
762df8dc-2dde-4a91-aae9-8bb5aff5f1e3	Home	home	Home / property insurance	t	2026-06-16 11:53:28.564033+00	2026-06-16 11:53:28.564033+00
3946f261-634c-4272-805e-d7bc1e785e0c	Personal Accident	personal_accident	Personal accident cover	t	2026-06-16 11:53:28.564033+00	2026-06-16 11:53:28.564033+00
ef695a11-24e6-483e-a104-c85fb8f80de1	Endowment	endowment	Endowment / savings plan	t	2026-06-16 11:53:28.564033+00	2026-06-16 11:53:28.564033+00
21663803-bfeb-4e29-87b5-89b1fc98c05e	Critical Illness	critical_illness	Critical illness cover	t	2026-06-16 11:55:04.582193+00	2026-06-16 11:55:04.582196+00
65c0afe2-f60d-4274-98a7-c910542048e7	Test Cyber	test_cyber_1781614105	Cyber insurance for testing	t	2026-06-16 12:48:25.384871+00	2026-06-16 12:48:25.384874+00
bd9ddda9-ecdb-40d1-a4c7-5fbb3d0077e8	Test Cyber f44edd25	test_cyber_f44edd25	Cyber insurance for testing	t	2026-06-16 12:49:54.129919+00	2026-06-16 12:49:54.129923+00
c578fd2e-0409-4802-ae1b-1aae9f83dff0	Test Cyber 10ca3fc5	test_cyber_10ca3fc5	Cyber insurance for testing	t	2026-06-16 12:50:54.343452+00	2026-06-16 12:50:54.343455+00
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.roles (id, role_name, role_type, is_active) FROM stdin;
4c249fd3-22d2-4626-a4c8-dbd7d16f4b4d	SUPERADMIN	ADMIN	t
7ed10139-2869-40db-b1d4-d29d9c88d641	CLAIMS_AGENT	ADMIN	t
c3d3b185-4f61-4b97-94ba-14a16a57488f	CUSTOMER	CUSTOMER	t
2588a7f0-6454-49e2-be25-597926c93602	READ_ONLY	CUSTOMER	t
332028fd-04a9-4f35-ada5-fcbf714c76ab	PARTNER	PARTNER	t
\.


--
-- Data for Name: user_activity; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_activity (id, user_id, first_login_at, last_login_at, login_count, has_logged_in, created_at, updated_at) FROM stdin;
ae24cc99-729d-447b-88ed-96b7f5887afe	b5569ec9-1a95-4969-9a97-a714e82c5ba7	2026-06-16 12:48:26.014346+00	2026-06-16 12:48:26.014346+00	1	t	2026-06-16 12:48:26.015817+00	2026-06-16 12:48:26.01582+00
bfad1b80-2c7f-42b7-9b4f-3dada5e0202e	b677f283-5b8d-42ae-bcb0-0af5808697c3	2026-06-16 12:50:54.979427+00	2026-06-16 12:50:54.979427+00	1	t	2026-06-16 12:50:54.98159+00	2026-06-16 12:50:54.981593+00
8051abe5-5213-4fb4-bada-4d82ddd25669	3f663e54-b4bb-4fa7-abf3-1b632a9f7893	2026-06-16 12:50:58.837871+00	2026-06-16 12:50:58.837871+00	1	t	2026-06-16 12:50:58.839264+00	2026-06-16 12:50:58.839267+00
7f32ca8b-d80b-4da7-8b3a-448bdc232c28	016370aa-3ed0-4aea-a065-f865aed9e245	2026-06-16 12:47:28.33058+00	2026-06-16 12:53:38.000011+00	6	t	2026-06-16 12:47:28.334002+00	2026-06-16 12:53:38.004154+00
d3e60883-3bcd-4f2b-a896-73866461bf08	4444a2f9-ad30-4414-8491-f4025b6f76ba	2026-06-16 15:48:21.873171+00	2026-06-17 10:26:28.413531+00	4	t	2026-06-16 15:48:21.879789+00	2026-06-17 10:26:28.416495+00
d9cf687b-0592-4b2f-a3ce-140e9141bee0	38eb24db-e6e4-4ade-8c8d-ac9942c6d9eb	2026-06-17 09:40:02.766679+00	2026-06-17 13:00:34.502802+00	5	t	2026-06-17 09:40:02.768705+00	2026-06-17 13:00:34.50382+00
71fc2afd-cd80-45f3-b591-b9c529a88195	cd32eb60-940a-4016-8a3d-1b3d251e3d27	2026-06-16 14:15:01.918899+00	2026-06-17 13:12:20.013479+00	9	t	2026-06-16 14:15:01.920074+00	2026-06-17 13:12:20.0149+00
2ac6226c-b0d7-422b-ae0c-a56933bbdd0a	c620c95b-ccde-436c-87c6-da3e331ca0bf	2026-06-17 09:29:26.432788+00	2026-06-17 18:19:12.158583+00	7	t	2026-06-17 09:29:26.43566+00	2026-06-17 18:19:12.159987+00
cff1d6ea-2a0e-4f2d-bd61-aa4ee96c2146	2d42b993-d396-4489-96b4-44baffa94828	2026-06-16 13:37:41.530398+00	2026-06-16 14:11:51.213925+00	5	t	2026-06-16 13:37:41.531282+00	2026-06-16 14:11:51.215004+00
679d4bfa-bd35-4d44-840a-929de03314de	c0b50711-22bf-4ea6-a7d7-f932591705fb	2026-06-16 13:38:03.625666+00	2026-06-16 14:48:33.700259+00	9	t	2026-06-16 13:38:03.627159+00	2026-06-16 14:48:33.701542+00
30f7623c-cdf6-477f-84c6-9bed3004d532	83f2ce28-c466-4687-98f1-24ab2340d531	2026-06-16 14:16:23.450139+00	2026-06-16 16:42:51.597326+00	4	t	2026-06-16 14:16:23.451004+00	2026-06-16 16:42:51.598905+00
feb7598a-dc7a-434d-96c6-78e0733dd67e	213c0630-327d-4b98-92c1-529d128fed8c	2026-06-16 13:31:35.196651+00	2026-06-17 07:21:32.701565+00	27	t	2026-06-16 13:31:35.19923+00	2026-06-17 07:21:32.704313+00
\.


--
-- Data for Name: user_roles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_roles (id, user_id, role_id, assigned_by, is_active, created_at) FROM stdin;
4235cc0d-7766-4c6a-b647-b9360e44b05b	213c0630-327d-4b98-92c1-529d128fed8c	4c249fd3-22d2-4626-a4c8-dbd7d16f4b4d	\N	t	2026-06-15 14:42:17.456595+00
5dd54996-e2c4-4124-aa51-7fa83b55c598	ed64ed3a-82fd-4070-94b4-48797e128065	c3d3b185-4f61-4b97-94ba-14a16a57488f	\N	t	2026-06-15 14:42:17.466503+00
c06a13eb-0206-405a-847c-b62bcfa7de1f	413e8f78-0fc9-40fd-a0cb-290bb769ae8a	c3d3b185-4f61-4b97-94ba-14a16a57488f	\N	t	2026-06-15 14:48:17.330957+00
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, email, name, user_type, is_active, is_deleted, created_at, updated_at, mobile_no) FROM stdin;
213c0630-327d-4b98-92c1-529d128fed8c	admin@easyclaims.com	Super Admin	SUPERADMIN	t	f	2026-06-15 14:42:17.442768+00	2026-06-15 14:42:17.442773+00	\N
ed64ed3a-82fd-4070-94b4-48797e128065	customer@easyclaims.com	Test Customer	CUSTOMER	t	f	2026-06-15 14:42:17.460852+00	2026-06-15 14:42:17.460855+00	\N
413e8f78-0fc9-40fd-a0cb-290bb769ae8a	newuser@easyclaims.com	New User	CUSTOMER	t	f	2026-06-15 14:48:17.323659+00	2026-06-15 14:48:17.323663+00	+91-9876543210
2d42b993-d396-4489-96b4-44baffa94828	partner@healthbridge.in	HealthBridge Brokers	PARTNER	t	f	2026-06-16 11:18:24.252783+00	2026-06-16 11:18:24.252786+00	\N
c0b50711-22bf-4ea6-a7d7-f932591705fb	rahul@example.com	Rahul Sharma	CUSTOMER	t	f	2026-06-16 11:18:24.317198+00	2026-06-16 11:18:24.317201+00	\N
016370aa-3ed0-4aea-a065-f865aed9e245	admin@easyclaims.in	Super Admin	SUPERADMIN	t	f	2026-06-16 12:42:46.911687+00	2026-06-16 12:42:46.911687+00	\N
b5569ec9-1a95-4969-9a97-a714e82c5ba7	partner_1781614104@test.com	Test Brokers Ltd	PARTNER	t	f	2026-06-16 12:48:25.435965+00	2026-06-16 12:48:25.435968+00	\N
b677f283-5b8d-42ae-bcb0-0af5808697c3	partner_342a5630@test.com	Test Brokers Ltd 342a5630	PARTNER	t	f	2026-06-16 12:50:54.392595+00	2026-06-16 12:50:54.392598+00	\N
3f663e54-b4bb-4fa7-abf3-1b632a9f7893	member_342a5630@test.com	Rahul Test Updated	CUSTOMER	t	f	2026-06-16 12:50:55.028792+00	2026-06-16 12:50:58.876861+00	+91-9876543210
4444a2f9-ad30-4414-8491-f4025b6f76ba	chinar.vartak@gmail.com	chinar	PARTNER	t	f	2026-06-16 13:54:36.531081+00	2026-06-16 13:54:36.531085+00	\N
cd32eb60-940a-4016-8a3d-1b3d251e3d27	chinarvartak@gmail.com	chinar	PARTNER	t	f	2026-06-16 14:14:46.021476+00	2026-06-16 14:14:46.021478+00	\N
83f2ce28-c466-4687-98f1-24ab2340d531	chinarartak@gmail.com	fsfs	CUSTOMER	t	f	2026-06-16 14:16:04.529703+00	2026-06-16 14:16:04.529706+00	575757575757
c620c95b-ccde-436c-87c6-da3e331ca0bf	chinarvartak6@gmail.com	Chinar Vartak	SUPERADMIN	t	f	2026-06-17 09:28:05.852776+00	2026-06-17 09:28:28.756219+00	\N
38eb24db-e6e4-4ade-8c8d-ac9942c6d9eb	workmytemp@gmail.com	Test chinar member	CUSTOMER	t	f	2026-06-17 09:39:28.184658+00	2026-06-17 09:39:28.184661+00	9637878885
\.


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: auth_sessions auth_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_sessions
    ADD CONSTRAINT auth_sessions_pkey PRIMARY KEY (session_id);


--
-- Name: dpdp_consents dpdp_consents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dpdp_consents
    ADD CONSTRAINT dpdp_consents_pkey PRIMARY KEY (id);


--
-- Name: email_templates email_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.email_templates
    ADD CONSTRAINT email_templates_pkey PRIMARY KEY (id);


--
-- Name: enrollment_history enrollment_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enrollment_history
    ADD CONSTRAINT enrollment_history_pkey PRIMARY KEY (id);


--
-- Name: family_members family_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.family_members
    ADD CONSTRAINT family_members_pkey PRIMARY KEY (id);


--
-- Name: member_enrollments member_enrollments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_enrollments
    ADD CONSTRAINT member_enrollments_pkey PRIMARY KEY (id);


--
-- Name: member_profiles member_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_profiles
    ADD CONSTRAINT member_profiles_pkey PRIMARY KEY (user_id);


--
-- Name: membership_plans membership_plans_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.membership_plans
    ADD CONSTRAINT membership_plans_name_key UNIQUE (name);


--
-- Name: membership_plans membership_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.membership_plans
    ADD CONSTRAINT membership_plans_pkey PRIMARY KEY (id);


--
-- Name: nominees nominees_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nominees
    ADD CONSTRAINT nominees_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: otp_log otp_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.otp_log
    ADD CONSTRAINT otp_log_pkey PRIMARY KEY (id);


--
-- Name: partner_plans partner_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.partner_plans
    ADD CONSTRAINT partner_plans_pkey PRIMARY KEY (id);


--
-- Name: partners partners_api_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.partners
    ADD CONSTRAINT partners_api_key_key UNIQUE (api_key);


--
-- Name: partners partners_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.partners
    ADD CONSTRAINT partners_pkey PRIMARY KEY (id);


--
-- Name: partners partners_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.partners
    ADD CONSTRAINT partners_user_id_key UNIQUE (user_id);


--
-- Name: policies policies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.policies
    ADD CONSTRAINT policies_pkey PRIMARY KEY (id);


--
-- Name: policies policies_policy_number_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.policies
    ADD CONSTRAINT policies_policy_number_key UNIQUE (policy_number);


--
-- Name: policy_family_members policy_family_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.policy_family_members
    ADD CONSTRAINT policy_family_members_pkey PRIMARY KEY (id);


--
-- Name: policy_types policy_types_code_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.policy_types
    ADD CONSTRAINT policy_types_code_key UNIQUE (code);


--
-- Name: policy_types policy_types_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.policy_types
    ADD CONSTRAINT policy_types_name_key UNIQUE (name);


--
-- Name: policy_types policy_types_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.policy_types
    ADD CONSTRAINT policy_types_pkey PRIMARY KEY (id);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: roles roles_role_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_role_name_key UNIQUE (role_name);


--
-- Name: member_enrollments uq_member_partner; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_enrollments
    ADD CONSTRAINT uq_member_partner UNIQUE (user_id, partner_id);


--
-- Name: partner_plans uq_partner_plan; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.partner_plans
    ADD CONSTRAINT uq_partner_plan UNIQUE (partner_id, plan_id);


--
-- Name: policy_family_members uq_policy_family_member; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.policy_family_members
    ADD CONSTRAINT uq_policy_family_member UNIQUE (policy_id, family_member_id);


--
-- Name: user_roles uq_user_role; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT uq_user_role UNIQUE (user_id, role_id);


--
-- Name: user_activity user_activity_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_activity
    ADD CONSTRAINT user_activity_pkey PRIMARY KEY (id);


--
-- Name: user_activity user_activity_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_activity
    ADD CONSTRAINT user_activity_user_id_key UNIQUE (user_id);


--
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_auth_sessions_jti; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_auth_sessions_jti ON public.auth_sessions USING btree (jti);


--
-- Name: ix_auth_sessions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_auth_sessions_user_id ON public.auth_sessions USING btree (user_id);


--
-- Name: ix_email_templates_slug; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_email_templates_slug ON public.email_templates USING btree (slug);


--
-- Name: ix_otp_log_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_otp_log_email ON public.otp_log USING btree (email);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: dpdp_consents dpdp_consents_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dpdp_consents
    ADD CONSTRAINT dpdp_consents_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: enrollment_history enrollment_history_enrollment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enrollment_history
    ADD CONSTRAINT enrollment_history_enrollment_id_fkey FOREIGN KEY (enrollment_id) REFERENCES public.member_enrollments(id);


--
-- Name: enrollment_history enrollment_history_from_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enrollment_history
    ADD CONSTRAINT enrollment_history_from_plan_id_fkey FOREIGN KEY (from_plan_id) REFERENCES public.membership_plans(id);


--
-- Name: enrollment_history enrollment_history_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enrollment_history
    ADD CONSTRAINT enrollment_history_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES public.partners(id);


--
-- Name: enrollment_history enrollment_history_to_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enrollment_history
    ADD CONSTRAINT enrollment_history_to_plan_id_fkey FOREIGN KEY (to_plan_id) REFERENCES public.membership_plans(id);


--
-- Name: enrollment_history enrollment_history_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.enrollment_history
    ADD CONSTRAINT enrollment_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: family_members family_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.family_members
    ADD CONSTRAINT family_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: member_enrollments member_enrollments_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_enrollments
    ADD CONSTRAINT member_enrollments_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES public.partners(id);


--
-- Name: member_enrollments member_enrollments_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_enrollments
    ADD CONSTRAINT member_enrollments_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES public.membership_plans(id);


--
-- Name: member_enrollments member_enrollments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_enrollments
    ADD CONSTRAINT member_enrollments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: member_profiles member_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.member_profiles
    ADD CONSTRAINT member_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: nominees nominees_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nominees
    ADD CONSTRAINT nominees_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: notifications notifications_recipient_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_recipient_user_id_fkey FOREIGN KEY (recipient_user_id) REFERENCES public.users(id);


--
-- Name: otp_log otp_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.otp_log
    ADD CONSTRAINT otp_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: partner_plans partner_plans_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.partner_plans
    ADD CONSTRAINT partner_plans_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES public.partners(id);


--
-- Name: partner_plans partner_plans_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.partner_plans
    ADD CONSTRAINT partner_plans_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES public.membership_plans(id);


--
-- Name: partners partners_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.partners
    ADD CONSTRAINT partners_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: policies policies_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.policies
    ADD CONSTRAINT policies_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES public.partners(id);


--
-- Name: policies policies_policy_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.policies
    ADD CONSTRAINT policies_policy_type_id_fkey FOREIGN KEY (policy_type_id) REFERENCES public.policy_types(id);


--
-- Name: policies policies_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.policies
    ADD CONSTRAINT policies_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: policy_family_members policy_family_members_family_member_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.policy_family_members
    ADD CONSTRAINT policy_family_members_family_member_id_fkey FOREIGN KEY (family_member_id) REFERENCES public.family_members(id);


--
-- Name: policy_family_members policy_family_members_policy_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.policy_family_members
    ADD CONSTRAINT policy_family_members_policy_id_fkey FOREIGN KEY (policy_id) REFERENCES public.policies(id);


--
-- Name: user_activity user_activity_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_activity
    ADD CONSTRAINT user_activity_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_roles user_roles_assigned_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES public.users(id);


--
-- Name: user_roles user_roles_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id);


--
-- Name: user_roles user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

\unrestrict WAzsCB6GQy5OO4ekwo8P0uDgMRHgLYlH3Awc3bbrxsH8Zqo8CZZj1ZquAqnSSrH


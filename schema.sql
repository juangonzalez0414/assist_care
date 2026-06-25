--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.5

-- Started on 2026-06-02 09:46:53

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
-- TOC entry 2 (class 3079 OID 16463)
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- TOC entry 4997 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- TOC entry 893 (class 1247 OID 16520)
-- Name: estado_peticion; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.estado_peticion AS ENUM (
    'activa',
    'asignada',
    'completada',
    'cancelada'
);


ALTER TYPE public.estado_peticion OWNER TO postgres;

--
-- TOC entry 896 (class 1247 OID 16530)
-- Name: estado_postulacion; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.estado_postulacion AS ENUM (
    'pendiente',
    'aceptada',
    'rechazada'
);


ALTER TYPE public.estado_postulacion OWNER TO postgres;

--
-- TOC entry 890 (class 1247 OID 16510)
-- Name: estado_verificacion; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.estado_verificacion AS ENUM (
    'preregistro',
    'pendiente_revision',
    'aprobado',
    'rechazado'
);


ALTER TYPE public.estado_verificacion OWNER TO postgres;

--
-- TOC entry 887 (class 1247 OID 16501)
-- Name: rol_usuario; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.rol_usuario AS ENUM (
    'super_admin',
    'admin',
    'discapacitado',
    'enfermero'
);


ALTER TYPE public.rol_usuario OWNER TO postgres;

--
-- TOC entry 899 (class 1247 OID 16538)
-- Name: sexo_tipo; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.sexo_tipo AS ENUM (
    'M',
    'F',
    'Otro'
);


ALTER TYPE public.sexo_tipo OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 219 (class 1259 OID 16557)
-- Name: perfil_discapacitado; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.perfil_discapacitado (
    usuario_id uuid NOT NULL,
    nombres character varying(100) NOT NULL,
    apellidos character varying(100) NOT NULL,
    cedula character varying(20) NOT NULL,
    ciudad character varying(100) NOT NULL,
    fecha_nacimiento date NOT NULL,
    sexo public.sexo_tipo NOT NULL,
    url_cedula character varying(500),
    url_certificado_discapacidad character varying(500),
    fecha_actualizacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.perfil_discapacitado OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 16572)
-- Name: perfil_enfermero; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.perfil_enfermero (
    usuario_id uuid NOT NULL,
    nombres character varying(100) NOT NULL,
    apellidos character varying(100) NOT NULL,
    cedula character varying(20) NOT NULL,
    ciudad character varying(100) NOT NULL,
    fecha_nacimiento date NOT NULL,
    sexo public.sexo_tipo NOT NULL,
    telefono_whatsapp character varying(20) NOT NULL,
    url_cedula character varying(500),
    url_tarjeta_profesional character varying(500),
    calificacion_promedio numeric(3,2) DEFAULT 5.00,
    fecha_actualizacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT perfil_enfermero_calificacion_promedio_check CHECK (((calificacion_promedio >= (0)::numeric) AND (calificacion_promedio <= (5)::numeric)))
);


ALTER TABLE public.perfil_enfermero OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 16589)
-- Name: peticiones; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.peticiones (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    discapacitado_id uuid NOT NULL,
    titulo character varying(150) NOT NULL,
    descripcion text NOT NULL,
    fecha_evento timestamp with time zone NOT NULL,
    ciudad character varying(100) NOT NULL,
    estado public.estado_peticion DEFAULT 'activa'::public.estado_peticion NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.peticiones OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 16604)
-- Name: postulaciones; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.postulaciones (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    peticion_id uuid NOT NULL,
    enfermero_id uuid NOT NULL,
    estado public.estado_postulacion DEFAULT 'pendiente'::public.estado_postulacion NOT NULL,
    fecha_postulacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.postulaciones OWNER TO postgres;

--
-- TOC entry 218 (class 1259 OID 16545)
-- Name: usuarios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuarios (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    rol public.rol_usuario NOT NULL,
    estado public.estado_verificacion DEFAULT 'preregistro'::public.estado_verificacion NOT NULL,
    fecha_creacion timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.usuarios OWNER TO postgres;

--
-- TOC entry 4828 (class 2606 OID 16566)
-- Name: perfil_discapacitado perfil_discapacitado_cedula_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.perfil_discapacitado
    ADD CONSTRAINT perfil_discapacitado_cedula_key UNIQUE (cedula);


--
-- TOC entry 4830 (class 2606 OID 16564)
-- Name: perfil_discapacitado perfil_discapacitado_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.perfil_discapacitado
    ADD CONSTRAINT perfil_discapacitado_pkey PRIMARY KEY (usuario_id);


--
-- TOC entry 4832 (class 2606 OID 16583)
-- Name: perfil_enfermero perfil_enfermero_cedula_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.perfil_enfermero
    ADD CONSTRAINT perfil_enfermero_cedula_key UNIQUE (cedula);


--
-- TOC entry 4834 (class 2606 OID 16581)
-- Name: perfil_enfermero perfil_enfermero_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.perfil_enfermero
    ADD CONSTRAINT perfil_enfermero_pkey PRIMARY KEY (usuario_id);


--
-- TOC entry 4837 (class 2606 OID 16598)
-- Name: peticiones peticiones_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.peticiones
    ADD CONSTRAINT peticiones_pkey PRIMARY KEY (id);


--
-- TOC entry 4839 (class 2606 OID 16611)
-- Name: postulaciones postulaciones_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.postulaciones
    ADD CONSTRAINT postulaciones_pkey PRIMARY KEY (id);


--
-- TOC entry 4841 (class 2606 OID 16613)
-- Name: postulaciones unica_postulacion; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.postulaciones
    ADD CONSTRAINT unica_postulacion UNIQUE (peticion_id, enfermero_id);


--
-- TOC entry 4824 (class 2606 OID 16556)
-- Name: usuarios usuarios_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_email_key UNIQUE (email);


--
-- TOC entry 4826 (class 2606 OID 16554)
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- TOC entry 4835 (class 1259 OID 16624)
-- Name: idx_peticiones_ciudad_estado; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_peticiones_ciudad_estado ON public.peticiones USING btree (ciudad, estado);


--
-- TOC entry 4822 (class 1259 OID 16625)
-- Name: idx_usuarios_email_estado; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_usuarios_email_estado ON public.usuarios USING btree (email, estado);


--
-- TOC entry 4842 (class 2606 OID 16567)
-- Name: perfil_discapacitado perfil_discapacitado_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.perfil_discapacitado
    ADD CONSTRAINT perfil_discapacitado_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- TOC entry 4843 (class 2606 OID 16584)
-- Name: perfil_enfermero perfil_enfermero_usuario_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.perfil_enfermero
    ADD CONSTRAINT perfil_enfermero_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- TOC entry 4844 (class 2606 OID 16599)
-- Name: peticiones peticiones_discapacitado_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.peticiones
    ADD CONSTRAINT peticiones_discapacitado_id_fkey FOREIGN KEY (discapacitado_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- TOC entry 4845 (class 2606 OID 16619)
-- Name: postulaciones postulaciones_enfermero_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.postulaciones
    ADD CONSTRAINT postulaciones_enfermero_id_fkey FOREIGN KEY (enfermero_id) REFERENCES public.usuarios(id) ON DELETE CASCADE;


--
-- TOC entry 4846 (class 2606 OID 16614)
-- Name: postulaciones postulaciones_peticion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.postulaciones
    ADD CONSTRAINT postulaciones_peticion_id_fkey FOREIGN KEY (peticion_id) REFERENCES public.peticiones(id) ON DELETE CASCADE;


-- Completed on 2026-06-02 09:46:53

--
-- PostgreSQL database dump complete
--


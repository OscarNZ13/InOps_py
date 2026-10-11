-- Esquema de la base InOps (SQL Server). Los cambios futuros van en scripts nuevos numerados (02_..., 03_...).

CREATE DATABASE InOps COLLATE Modern_Spanish_CI_AI;
GO

USE InOps;
GO

-- Catálogo de roles con ids fijos en todos los entornos
CREATE TABLE dbo.Roles (
    id_role      TINYINT        NOT NULL,
    name         VARCHAR(20)    NOT NULL,
    Description  NVARCHAR(100)  NULL,
    IsActive     BIT            NOT NULL CONSTRAINT df_Roles_IsActive  DEFAULT 1,
    CreatedAt    DATETIME2      NOT NULL CONSTRAINT df_Roles_CreatedAt DEFAULT SYSDATETIME(),
    CONSTRAINT pk_Roles      PRIMARY KEY (id_role),
    CONSTRAINT uq_Roles_name UNIQUE (name)
);
GO

INSERT INTO dbo.Roles (id_role, name, Description) VALUES
    (1, 'admin', N'Administrador del sistema'),
    (2, 'rrhh',  N'Recursos Humanos'),
    (3, 'dcc',   N'DCC');
GO

-- Usuarios que inician sesión en el sistema
CREATE TABLE dbo.Users (
    id_user        INT IDENTITY(1,1) NOT NULL,
    username       NVARCHAR(50)  NOT NULL,
    password_hash  VARCHAR(255)  NOT NULL,
    id_role        TINYINT       NOT NULL CONSTRAINT df_Users_id_role   DEFAULT 3,
    IsActive       BIT           NOT NULL CONSTRAINT df_Users_IsActive  DEFAULT 1,
    CreatedAt      DATETIME2     NOT NULL CONSTRAINT df_Users_CreatedAt DEFAULT SYSDATETIME(),
    UpdatedAt      DATETIME2     NOT NULL CONSTRAINT df_Users_UpdatedAt DEFAULT SYSDATETIME(),
    CONSTRAINT pk_Users          PRIMARY KEY (id_user),
    CONSTRAINT uq_Users_username UNIQUE (username),
    CONSTRAINT fk_Users_Roles
        FOREIGN KEY (id_role) REFERENCES dbo.Roles(id_role)
);
GO

-- Datos personales de los colaboradores. No se borran: se desactivan con IsActive = 0
CREATE TABLE dbo.Collaborators (
    id_collab       INT IDENTITY(1,1) NOT NULL,
    FirstName       NVARCHAR(50)  NOT NULL,
    SecondName      NVARCHAR(50)  NULL,
    LastName        NVARCHAR(50)  NOT NULL,
    SecondLastName  NVARCHAR(50)  NULL,
    Birthdate       DATE          NOT NULL,
    IsActive        BIT           NOT NULL CONSTRAINT df_Collaborators_IsActive  DEFAULT 1,
    CreatedAt       DATETIME2     NOT NULL CONSTRAINT df_Collaborators_CreatedAt DEFAULT SYSDATETIME(),
    UpdatedAt       DATETIME2     NOT NULL CONSTRAINT df_Collaborators_UpdatedAt DEFAULT SYSDATETIME(),
    CONSTRAINT pk_Collaborators           PRIMARY KEY (id_collab),
    CONSTRAINT ck_Collaborators_Birthdate CHECK (Birthdate <= CAST(GETDATE() AS DATE))
);
GO

-- Perfil 1 a 1 con Collaborators. Initials y Signature son únicos y no cambian después de crearse
CREATE TABLE dbo.CollaboratorProfiles (
    id_profile   INT IDENTITY(1,1) NOT NULL,
    id_collab    INT            NOT NULL,
    Initials     NVARCHAR(20)   NOT NULL,
    Signature    NVARCHAR(60)   NOT NULL,
    Position     NVARCHAR(100)  NULL,
    Department   NVARCHAR(100)  NULL,
    Email        NVARCHAR(100)  NULL,
    Phone        NVARCHAR(20)   NULL,
    CreatedAt    DATETIME2      NOT NULL CONSTRAINT df_CollaboratorProfiles_CreatedAt DEFAULT SYSDATETIME(),
    UpdatedAt    DATETIME2      NOT NULL CONSTRAINT df_CollaboratorProfiles_UpdatedAt DEFAULT SYSDATETIME(),
    CONSTRAINT pk_CollaboratorProfiles           PRIMARY KEY (id_profile),
    CONSTRAINT uq_CollaboratorProfiles_id_collab UNIQUE (id_collab),
    CONSTRAINT uq_CollaboratorProfiles_Initials  UNIQUE (Initials),
    CONSTRAINT uq_CollaboratorProfiles_Signature UNIQUE (Signature),
    CONSTRAINT fk_CollaboratorProfiles_Collaborators
        FOREIGN KEY (id_collab) REFERENCES dbo.Collaborators(id_collab)
);
GO

-- Email único solo cuando tiene valor (permite varios perfiles sin correo)
CREATE UNIQUE INDEX ux_CollaboratorProfiles_Email
    ON dbo.CollaboratorProfiles(Email) WHERE Email IS NOT NULL;
GO

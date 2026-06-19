USE Rossmann;
GO

IF OBJECT_ID('dbo.Conversations', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.Conversations (
        Id          INT IDENTITY(1,1)  NOT NULL PRIMARY KEY,
        SessionId   VARCHAR(36)        NOT NULL,  -- UUID generated per CLI session
        TurnOrder   INT                NOT NULL,  -- 0-based index within the session
        Question    NVARCHAR(MAX)      NOT NULL,
        SqlQuery    NVARCHAR(MAX)      NULL,
        Answer      NVARCHAR(MAX)      NULL,
        [RowCount]  INT                NULL,
        Rating      INT                NULL,      -- 1 = thumbs up, -1 = thumbs down, NULL = no feedback
        CreatedAt   DATETIME           NOT NULL DEFAULT GETDATE()
    );

    CREATE INDEX IX_Conversations_SessionId ON dbo.Conversations (SessionId);
END
GO

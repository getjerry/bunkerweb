from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    LargeBinary,
    SmallInteger,
    String,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()
CONTEXTS_ENUM = Enum("global", "multisite")
SETTINGS_TYPES_ENUM = Enum("text", "check", "select")
METHODS_ENUM = Enum("ui", "scheduler", "autoconf")
SCHEDULES_ENUM = Enum("once", "minute", "hour", "day", "week")
CUSTOM_CONFIGS_TYPES = Enum(
    "http",
    "default_server_http",
    "server_http",
    "modsec",
    "modsec_crs",
    "stream",
    "stream_http",
)
LOG_LEVELS_ENUM = Enum("DEBUG", "INFO", "WARNING", "ERROR")
INTEGRATIONS_ENUM = Enum(
    "Docker",
    "Linux",
    "Swarm",
    "Kubernetes",
    "Autoconf",
    "Ansible",
    "Vagrant",
    "Unknown",
)


class Plugins(Base):
    __tablename__ = "plugins"

    id = Column(String(64), primary_key=True)
    order = Column(Integer, nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(String(255), nullable=False)
    version = Column(String(32), nullable=False)
    cache = Column(LargeBinary(length=(2**32) - 1), nullable=True)
    cache_last_update = Column(DateTime, nullable=True)
    cache_checksum = Column(String(255), nullable=True)

    settings = relationship(
        "Settings", back_populates="plugin", cascade="all, delete, delete-orphan"
    )
    jobs = relationship("Jobs", back_populates="plugin", cascade="all, delete")


class Settings(Base):
    __tablename__ = "settings"

    id = Column(String(255), primary_key=True)
    name = Column(String(255), primary_key=True)
    plugin_id = Column(
        String(64),
        ForeignKey("plugins.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    context = Column(CONTEXTS_ENUM, nullable=False)
    default = Column(String(1023), nullable=False)
    help = Column(String(255), nullable=False)
    label = Column(String(255), nullable=True)
    regex = Column(String(255), nullable=False)
    type = Column(SETTINGS_TYPES_ENUM, nullable=False)
    multiple = Column(String(255), nullable=True)

    selects = relationship("Selects", back_populates="setting", cascade="all, delete")
    services = relationship(
        "Services_settings", back_populates="setting", cascade="all, delete"
    )
    global_value = relationship(
        "Global_values", back_populates="setting", cascade="all, delete"
    )
    plugin = relationship("Plugins", back_populates="settings")


class Global_values(Base):
    __tablename__ = "global_values"

    setting_id = Column(
        String(255),
        ForeignKey("settings.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    value = Column(String(1023), nullable=False)
    suffix = Column(SmallInteger, primary_key=True, nullable=True, default=0)

    setting = relationship("Settings", back_populates="global_value")


class Services(Base):
    __tablename__ = "services"

    id = Column(String(64), primary_key=True)
    method = Column(METHODS_ENUM, nullable=False)

    settings = relationship(
        "Services_settings", back_populates="service", cascade="all, delete"
    )
    custom_configs = relationship(
        "Custom_configs", back_populates="service", cascade="all, delete"
    )


class Services_settings(Base):
    __tablename__ = "services_settings"

    service_id = Column(
        String(64),
        ForeignKey("services.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    setting_id = Column(
        String(255),
        ForeignKey("settings.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    value = Column(String(1023), nullable=False)
    suffix = Column(SmallInteger, primary_key=True, nullable=True, default=0)

    service = relationship("Services", back_populates="settings")
    setting = relationship("Settings", back_populates="services")


class Jobs(Base):
    __tablename__ = "jobs"

    plugin_id = Column(
        String(64),
        ForeignKey("plugins.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    name = Column(String(128), primary_key=True)
    file = Column(String(255), nullable=False)
    every = Column(SCHEDULES_ENUM, nullable=False)
    reload = Column(Boolean, nullable=False)
    last_run = Column(DateTime, nullable=True)

    plugin = relationship("Plugins", back_populates="jobs")


class Custom_configs(Base):
    __tablename__ = "custom_configs"

    id = Column(Integer, primary_key=True)
    service_id = Column(
        String(64),
        ForeignKey("services.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=True,
    )
    type = Column(CUSTOM_CONFIGS_TYPES, nullable=False)
    name = Column(String(255), nullable=False)
    data = Column(LargeBinary(length=(2**32) - 1), nullable=False)
    method = Column(METHODS_ENUM, nullable=False)

    service = relationship("Services", back_populates="custom_configs")


class Selects(Base):
    __tablename__ = "selects"

    setting_id = Column(
        String(255),
        ForeignKey("settings.id", onupdate="CASCADE", ondelete="CASCADE"),
        primary_key=True,
    )
    value = Column(String(255), primary_key=True)

    setting = relationship("Settings", back_populates="selects")


class Logs(Base):
    __tablename__ = "logs"

    id = Column(TIMESTAMP, primary_key=True)
    message = Column(String(1023), nullable=False)
    level = Column(LOG_LEVELS_ENUM, nullable=False)
    component = Column(String(255), nullable=False)


class Metadata(Base):
    __tablename__ = "metadata"

    id = Column(Integer, primary_key=True, default=1)
    is_initialized = Column(Boolean, nullable=False)
    first_config_saved = Column(Boolean, nullable=False)
    integration = Column(INTEGRATIONS_ENUM, nullable=False)
    version = Column(String(5), nullable=False)
import React, { useEffect, useState } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Select,
  DatePicker,
  Row,
  Col,
  Statistic,
  message,
  Popconfirm,
  Typography,
  Tooltip,
} from 'antd'
import {
  ReloadOutlined,
  DeleteOutlined,
  DownloadOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  BugOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { logApi } from '../services/api'

const { RangePicker } = DatePicker
const { Text } = Typography

interface Log {
  id: number
  level: string
  module: string
  message: string
  details: string
  created_at: string
}

interface LogFile {
  name: string
  size: number
  modified_at: string
}

interface LogStats {
  by_level: Record<string, number>
  by_module: Record<string, number>
}

const Logs: React.FC = () => {
  const [logs, setLogs] = useState<Log[]>([])
  const [logFiles, setLogFiles] = useState<LogFile[]>([])
  const [stats, setStats] = useState<LogStats>({ by_level: {}, by_module: {} })
  const [loading, setLoading] = useState(false)
  const [level, setLevel] = useState<string | undefined>(undefined)
  const [module, setModule] = useState<string | undefined>(undefined)
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    loadLogs()
  }, [level, module, dateRange])

  const loadData = async () => {
    await Promise.all([loadLogs(), loadLogFiles(), loadStats()])
  }

  const loadLogs = async () => {
    try {
      setLoading(true)
      const params: Record<string, string | number> = { limit: 200 }

      if (level) params.level = level
      if (module) params.module = module
      if (dateRange) {
        params.start_time = dateRange[0].toISOString()
        params.end_time = dateRange[1].toISOString()
      }

      const data = await logApi.getLogs(params) as Log[]
      setLogs(data)
    } catch (error: unknown) {
      message.error((error as Error).message || '加载日志失败')
    } finally {
      setLoading(false)
    }
  }

  const loadLogFiles = async () => {
    try {
      const data = await logApi.getLogFiles() as { files: LogFile[] }
      setLogFiles(data.files)
    } catch (error) {
      // ignore
    }
  }

  const loadStats = async () => {
    try {
      const data = await logApi.getLogStats(24) as LogStats
      setStats(data)
    } catch (error) {
      // ignore
    }
  }

  const clearOldLogs = async (days: number) => {
    try {
      const result = await logApi.clearOldLogs(days) as { message: string }
      message.success(result.message)
      loadData()
    } catch (error: unknown) {
      message.error((error as Error).message || '清理失败')
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const getLevelIcon = (level: string) => {
    const icons: Record<string, React.ReactNode> = {
      INFO: <InfoCircleOutlined style={{ color: '#1890ff' }} />,
      WARNING: <WarningOutlined style={{ color: '#faad14' }} />,
      ERROR: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />,
      DEBUG: <BugOutlined style={{ color: '#8c8c8c' }} />,
      SUCCESS: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
    }
    return icons[level] || <InfoCircleOutlined />
  }

  const getLevelTag = (level: string) => {
    const colorMap: Record<string, string> = {
      INFO: 'blue',
      WARNING: 'orange',
      ERROR: 'red',
      DEBUG: 'default',
      SUCCESS: 'green',
    }
    return (
      <Tag color={colorMap[level] || 'default'} icon={getLevelIcon(level)}>
        {level}
      </Tag>
    )
  }

  const columns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text: string) => (
        <Text style={{ fontSize: 12 }}>
          {new Date(text).toLocaleString('zh-CN')}
        </Text>
      ),
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      width: 100,
      render: getLevelTag,
    },
    {
      title: '模块',
      dataIndex: 'module',
      key: 'module',
      width: 120,
      render: (text: string) => (
        <Tag color="cyan">{text || 'system'}</Tag>
      ),
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
      render: (text: string) => (
        <Tooltip title={text}>
          <Text style={{ maxWidth: 400 }} ellipsis>
            {text}
          </Text>
        </Tooltip>
      ),
    },
  ]

  const fileColumns = [
    {
      title: '文件名',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      width: 120,
      render: formatFileSize,
    },
    {
      title: '修改时间',
      dataIndex: 'modified_at',
      key: 'modified_at',
      width: 180,
      render: (text: string) => new Date(text).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_: unknown, record: LogFile) => (
        <Button
          type="link"
          icon={<DownloadOutlined />}
          href={`/api/logs/files/${record.name}`}
          target="_blank"
        >
          下载
        </Button>
      ),
    },
  ]

  const modules = [...new Set(logs.map(l => l.module).filter(Boolean))]

  return (
    <div className="fade-in">
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={6}>
          <Card hoverable className="hover-card">
            <Statistic
              title="INFO"
              value={stats.by_level?.INFO || 0}
              prefix={<InfoCircleOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card hoverable className="hover-card">
            <Statistic
              title="WARNING"
              value={stats.by_level?.WARNING || 0}
              prefix={<WarningOutlined style={{ color: '#faad14' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card hoverable className="hover-card">
            <Statistic
              title="ERROR"
              value={stats.by_level?.ERROR || 0}
              prefix={<CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card hoverable className="hover-card">
            <Statistic
              title="SUCCESS"
              value={stats.by_level?.SUCCESS || 0}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title="系统日志"
        style={{ marginTop: 16 }}
        extra={
          <Space>
            <Select
              placeholder="日志级别"
              allowClear
              style={{ width: 120 }}
              value={level}
              onChange={setLevel}
              options={[
                { value: 'DEBUG', label: 'DEBUG' },
                { value: 'INFO', label: 'INFO' },
                { value: 'WARNING', label: 'WARNING' },
                { value: 'ERROR', label: 'ERROR' },
                { value: 'SUCCESS', label: 'SUCCESS' },
              ]}
            />
            <Select
              placeholder="模块"
              allowClear
              style={{ width: 120 }}
              value={module}
              onChange={setModule}
              options={modules.map(m => ({ value: m, label: m }))}
            />
            <RangePicker
              showTime
              value={dateRange}
              onChange={(dates) => setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs] | null)}
            />
            <Button icon={<ReloadOutlined />} onClick={loadData}>
              刷新
            </Button>
            <Popconfirm
              title="清理30天前的日志？"
              onConfirm={() => clearOldLogs(30)}
              okText="确定"
              cancelText="取消"
            >
              <Button icon={<DeleteOutlined />}>清理旧日志</Button>
            </Popconfirm>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={logs}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: total => `共 ${total} 条日志`,
            defaultPageSize: 50,
          }}
          size="small"
        />
      </Card>

      <Card title="日志文件" style={{ marginTop: 16 }}>
        <Table
          columns={fileColumns}
          dataSource={logFiles}
          rowKey="name"
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  )
}

export default Logs

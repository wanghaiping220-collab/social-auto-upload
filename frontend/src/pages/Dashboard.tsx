import React, { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Table, Tag, Space, message } from 'antd'
import {
  UserOutlined,
  CloudUploadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { accountApi, contentApi, publishApi, logApi } from '../services/api'

interface Stats {
  accounts: number
  contents: number
  publishStats: {
    total: number
    pending: number
    uploading: number
    published: number
    failed: number
  }
}

interface RecentLog {
  id: number
  level: string
  module: string
  message: string
  created_at: string
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<Stats>({
    accounts: 0,
    contents: 0,
    publishStats: {
      total: 0,
      pending: 0,
      uploading: 0,
      published: 0,
      failed: 0,
    },
  })
  const [recentLogs, setRecentLogs] = useState<RecentLog[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [accounts, contents, publishStats, logs] = await Promise.all([
        accountApi.getAccounts() as Promise<unknown[]>,
        contentApi.getContents() as Promise<unknown[]>,
        publishApi.getStats() as Promise<Stats['publishStats']>,
        logApi.getRecentLogs({ minutes: 60 }) as Promise<RecentLog[]>,
      ])

      setStats({
        accounts: accounts.length,
        contents: contents.length,
        publishStats,
      })
      setRecentLogs(logs.slice(0, 10))
    } catch (error) {
      message.error('加载数据失败')
    } finally {
      setLoading(false)
    }
  }

  const logColumns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text: string) => new Date(text).toLocaleString('zh-CN'),
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      width: 100,
      render: (level: string) => {
        const colorMap: Record<string, string> = {
          INFO: 'blue',
          WARNING: 'orange',
          ERROR: 'red',
          DEBUG: 'gray',
          SUCCESS: 'green',
        }
        return <Tag color={colorMap[level] || 'default'}>{level}</Tag>
      },
    },
    {
      title: '模块',
      dataIndex: 'module',
      key: 'module',
      width: 120,
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
    },
  ]

  return (
    <div className="fade-in">
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable className="hover-card">
            <Statistic
              title="账号数量"
              value={stats.accounts}
              prefix={<UserOutlined style={{ color: '#1890ff' }} />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable className="hover-card">
            <Statistic
              title="内容数量"
              value={stats.contents}
              prefix={<CloudUploadOutlined style={{ color: '#722ed1' }} />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable className="hover-card">
            <Statistic
              title="发布成功"
              value={stats.publishStats.published}
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card hoverable className="hover-card">
            <Statistic
              title="发布失败"
              value={stats.publishStats.failed}
              prefix={<CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="发布任务统计" hoverable>
            <Space size="large" wrap>
              <Statistic
                title="待发布"
                value={stats.publishStats.pending}
                prefix={<ClockCircleOutlined style={{ color: '#1890ff' }} />}
                loading={loading}
              />
              <Statistic
                title="发布中"
                value={stats.publishStats.uploading}
                prefix={<SyncOutlined spin style={{ color: '#722ed1' }} />}
                loading={loading}
              />
              <Statistic
                title="已发布"
                value={stats.publishStats.published}
                prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                loading={loading}
              />
              <Statistic
                title="失败"
                value={stats.publishStats.failed}
                prefix={<CloseCircleOutlined style={{ color: '#ff4d4f' }} />}
                loading={loading}
              />
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="平台支持" hoverable>
            <Space size="middle">
              <Tag className="platform-tag-douyin" style={{ padding: '4px 12px', fontSize: 14 }}>
                抖音
              </Tag>
              <Tag className="platform-tag-weixin" style={{ padding: '4px 12px', fontSize: 14 }}>
                视频号
              </Tag>
              <Tag className="platform-tag-xiaohongshu" style={{ padding: '4px 12px', fontSize: 14 }}>
                小红书
              </Tag>
            </Space>
          </Card>
        </Col>
      </Row>

      <Card title="最近日志" style={{ marginTop: 16 }} hoverable>
        <Table
          columns={logColumns}
          dataSource={recentLogs}
          rowKey="id"
          pagination={false}
          size="small"
          loading={loading}
        />
      </Card>
    </div>
  )
}

export default Dashboard

import React, { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Layout, Menu, theme } from 'antd'
import {
  UserOutlined,
  CloudUploadOutlined,
  SendOutlined,
  FileTextOutlined,
  DashboardOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'

import Dashboard from './pages/Dashboard'
import AccountsPage from './pages/Accounts'
import ContentsPage from './pages/Contents'
import PublishPage from './pages/Publish'
import LogsPage from './pages/Logs'

const { Header, Sider, Content } = Layout

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/accounts', icon: <UserOutlined />, label: '账号管理' },
  { key: '/contents', icon: <CloudUploadOutlined />, label: '内容管理' },
  { key: '/publish', icon: <SendOutlined />, label: '发布中心' },
  { key: '/logs', icon: <FileTextOutlined />, label: '系统日志' },
]

const AppLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="dark"
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div className="logo-container">
          <SendOutlined style={{ fontSize: 24, color: 'white' }} />
          {!collapsed && <span className="logo-text">社媒分发系统</span>}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: 'all 0.2s' }}>
        <Header
          style={{
            padding: '0 24px',
            background: colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 4px rgba(0, 0, 0, 0.08)',
          }}
        >
          <h2 style={{ margin: 0, fontSize: 18 }}>
            {menuItems.find(item => item.key === location.pathname)?.label || '仪表盘'}
          </h2>
        </Header>
        <Content
          style={{
            margin: '24px',
            padding: 24,
            minHeight: 280,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
          }}
        >
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/accounts" element={<AccountsPage />} />
            <Route path="/contents" element={<ContentsPage />} />
            <Route path="/publish" element={<PublishPage />} />
            <Route path="/logs" element={<LogsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  )
}

export default App

# Admin Analytics Dashboard - Frontend Implementation Plan

**Target:** Build a comprehensive admin dashboard for platform owner visibility into customers, revenue, and usage metrics.

**Timeline Estimate:** 2-3 days for complete implementation

**Backend Status:** ✅ Complete - All 6 analytics endpoints are live and tested

---

## Table of Contents

1. [Overview](#overview)
2. [Phase 1: Core Dashboard (Day 1)](#phase-1-core-dashboard-day-1)
3. [Phase 2: Customer Management (Day 2)](#phase-2-customer-management-day-2)
4. [Phase 3: Revenue Analytics (Day 3)](#phase-3-revenue-analytics-day-3)
5. [API Reference](#api-reference)
6. [Component Architecture](#component-architecture)
7. [Testing Checklist](#testing-checklist)

---

## Overview

### What You're Building

An **admin-only dashboard** that provides complete visibility into:
- 📊 **Business Metrics**: MRR, ARR, customer count, growth rate
- 👥 **Customer Management**: Searchable/filterable customer list
- 🎯 **Upsell Opportunities**: Customers ready to upgrade
- ⚠️ **Health Alerts**: Failed payments, customers at quota limits
- 📈 **Revenue Trends**: 6-month revenue chart with tier breakdown

### Who Can Access

- ✅ Users with `admin` role only
- ❌ Regular users cannot see this dashboard
- Check: `user.roles.includes('admin')` from JWT token

### Navigation

Add to admin menu:
```
Admin Menu:
├── Dashboard (existing)
├── Analytics (NEW) ← Add this
├── Users
├── Settings
└── Backups
```

---

## Phase 1: Core Dashboard (Day 1)

**Goal:** Display key platform metrics and health indicators

**Time Estimate:** 4-6 hours

### Step 1.1: Create Analytics Page Route (30 min)

**File:** `src/pages/admin/AnalyticsPage.tsx`

```typescript
import { useState, useEffect } from 'react';
import { useAnalytics } from '@/hooks/useAnalytics';
import MetricsGrid from '@/components/analytics/MetricsGrid';
import HealthAlerts from '@/components/analytics/HealthAlerts';
import TierChart from '@/components/analytics/TierChart';

export default function AnalyticsPage() {
  const { overview, health, isLoading } = useAnalytics();

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Platform Analytics</h1>

      {/* Key Metrics Cards */}
      <MetricsGrid data={overview} />

      {/* Health Alerts */}
      <HealthAlerts data={health} />

      {/* Tier Distribution Chart */}
      <TierChart data={overview?.by_tier} />
    </div>
  );
}
```

**Add Route:**

```typescript
// src/App.tsx or routes config
{
  path: '/admin/analytics',
  element: <ProtectedRoute roles={['admin']}><AnalyticsPage /></ProtectedRoute>
}
```

---

### Step 1.2: Create Analytics Hook (1 hour)

**File:** `src/hooks/useAnalytics.ts`

```typescript
import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_BASE_URL;

interface AnalyticsOverview {
  total_tenants: number;
  by_tier: Record<string, number>;
  active_tenants: number;
  suspended_tenants: number;
  mrr: number;
  signups_last_30_days: number;
}

interface PlatformHealth {
  failed_payments_count: number;
  suspended_count: number;
  revenue_at_risk: number;
  high_value_customers: Array<{
    tenant_id: number;
    email: string;
    company_name: string;
    tier: string;
    mrr: number;
  }>;
  upsell_opportunities: Array<{
    tenant_id: number;
    email: string;
    current_tier: string;
    suggested_tier: string;
    usage_percent: number;
  }>;
}

export function useAnalytics() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [health, setHealth] = useState<PlatformHealth | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('authToken');
      const headers = { Authorization: `Bearer ${token}` };

      const [overviewRes, healthRes] = await Promise.all([
        axios.get(`${API_URL}/admin/analytics/overview`, { headers }),
        axios.get(`${API_URL}/admin/analytics/health`, { headers })
      ]);

      setOverview(overviewRes.data);
      setHealth(healthRes.data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch analytics');
      console.error('Analytics fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return { overview, health, isLoading, error, refetch: fetchAnalytics };
}
```

---

### Step 1.3: Create Metrics Grid Component (1 hour)

**File:** `src/components/analytics/MetricsGrid.tsx`

```typescript
interface MetricsGridProps {
  data: {
    total_tenants: number;
    active_tenants: number;
    mrr: number;
    signups_last_30_days: number;
    by_tier: Record<string, number>;
  };
}

export default function MetricsGrid({ data }: MetricsGridProps) {
  const metrics = [
    {
      label: 'Total Customers',
      value: data.total_tenants.toLocaleString(),
      trend: `${data.signups_last_30_days} new this month`,
      icon: '👥',
      color: 'blue'
    },
    {
      label: 'Active Customers',
      value: data.active_tenants.toLocaleString(),
      trend: `${((data.active_tenants / data.total_tenants) * 100).toFixed(1)}% active`,
      icon: '✅',
      color: 'green'
    },
    {
      label: 'Monthly Revenue (MRR)',
      value: `$${data.mrr.toLocaleString()}`,
      trend: `$${(data.mrr * 12).toLocaleString()} ARR`,
      icon: '💰',
      color: 'emerald'
    },
    {
      label: 'Paying Customers',
      value: (data.by_tier.starter + data.by_tier.business + data.by_tier.enterprise).toLocaleString(),
      trend: `${data.by_tier.free} on free tier`,
      icon: '💳',
      color: 'purple'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric) => (
        <div
          key={metric.label}
          className={`bg-white rounded-lg shadow p-6 border-l-4 border-${metric.color}-500`}
        >
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-gray-600">{metric.label}</p>
            <span className="text-2xl">{metric.icon}</span>
          </div>
          <p className="text-3xl font-bold text-gray-900">{metric.value}</p>
          <p className="text-sm text-gray-500 mt-1">{metric.trend}</p>
        </div>
      ))}
    </div>
  );
}
```

---

### Step 1.4: Create Health Alerts Component (1.5 hours)

**File:** `src/components/analytics/HealthAlerts.tsx`

```typescript
import { Link } from 'react-router-dom';

interface HealthAlertsProps {
  data: {
    failed_payments_count: number;
    suspended_count: number;
    revenue_at_risk: number;
    upsell_opportunities: Array<{
      tenant_id: number;
      email: string;
      current_tier: string;
      suggested_tier: string;
      usage_percent: number;
    }>;
  };
}

export default function HealthAlerts({ data }: HealthAlertsProps) {
  const hasAlerts = data.failed_payments_count > 0 ||
                    data.suspended_count > 0 ||
                    data.upsell_opportunities.length > 0;

  if (!hasAlerts) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <div className="flex items-center gap-3">
          <span className="text-3xl">✅</span>
          <div>
            <h3 className="text-lg font-semibold text-green-900">All Systems Healthy</h3>
            <p className="text-sm text-green-700">No payment issues or critical alerts</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">Platform Health</h2>

      {/* Failed Payments Alert */}
      {data.failed_payments_count > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <span className="text-2xl">⚠️</span>
            <div className="flex-1">
              <h4 className="font-semibold text-red-900">Failed Payments</h4>
              <p className="text-sm text-red-700">
                {data.failed_payments_count} customer{data.failed_payments_count > 1 ? 's' : ''} with payment issues
              </p>
              <p className="text-sm text-red-600 mt-1">
                Revenue at risk: ${data.revenue_at_risk.toFixed(2)}/month
              </p>
            </div>
            <Link
              to="/admin/analytics/customers?status=suspended"
              className="text-sm text-red-600 hover:text-red-800 font-medium"
            >
              View →
            </Link>
          </div>
        </div>
      )}

      {/* Upsell Opportunities */}
      {data.upsell_opportunities.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <span className="text-2xl">📈</span>
            <div className="flex-1">
              <h4 className="font-semibold text-blue-900">Upsell Opportunities</h4>
              <p className="text-sm text-blue-700 mb-3">
                {data.upsell_opportunities.length} customer{data.upsell_opportunities.length > 1 ? 's' : ''} ready to upgrade
              </p>

              {/* Show top 3 opportunities */}
              <div className="space-y-2">
                {data.upsell_opportunities.slice(0, 3).map((opp) => (
                  <div key={opp.tenant_id} className="bg-white rounded p-3 text-sm">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-900">{opp.email}</p>
                        <p className="text-gray-600">
                          {opp.current_tier} → {opp.suggested_tier}
                          <span className="ml-2 text-blue-600">({opp.usage_percent.toFixed(0)}% usage)</span>
                        </p>
                      </div>
                      <button className="text-blue-600 hover:text-blue-800 font-medium">
                        Contact
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {data.upsell_opportunities.length > 3 && (
                <Link
                  to="/admin/analytics/customers?tier=starter&sort=usage_desc"
                  className="text-sm text-blue-600 hover:text-blue-800 font-medium mt-2 inline-block"
                >
                  View all {data.upsell_opportunities.length} opportunities →
                </Link>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

### Step 1.5: Create Tier Distribution Chart (1.5 hours)

**File:** `src/components/analytics/TierChart.tsx`

**Install Chart Library:**
```bash
npm install recharts
```

```typescript
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface TierChartProps {
  data: Record<string, number>;
}

const TIER_COLORS = {
  free: '#9CA3AF',      // Gray
  starter: '#3B82F6',   // Blue
  business: '#8B5CF6',  // Purple
  enterprise: '#10B981' // Green
};

const TIER_LABELS = {
  free: 'Free',
  starter: 'Starter ($14.99)',
  business: 'Business ($79)',
  enterprise: 'Enterprise ($499)'
};

export default function TierChart({ data }: TierChartProps) {
  const chartData = Object.entries(data).map(([tier, count]) => ({
    name: TIER_LABELS[tier as keyof typeof TIER_LABELS],
    value: count,
    color: TIER_COLORS[tier as keyof typeof TIER_COLORS]
  }));

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">Customer Distribution by Tier</h2>

      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={100}
            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>

      {/* Summary Table */}
      <div className="mt-6 border-t pt-4">
        <table className="w-full text-sm">
          <tbody>
            {chartData.map((tier) => (
              <tr key={tier.name} className="border-b last:border-0">
                <td className="py-2">
                  <span className="inline-block w-3 h-3 rounded-full mr-2" style={{ backgroundColor: tier.color }} />
                  {tier.name}
                </td>
                <td className="py-2 text-right font-medium">{tier.value.toLocaleString()}</td>
                <td className="py-2 text-right text-gray-600">
                  {((tier.value / Object.values(data).reduce((a, b) => a + b, 0)) * 100).toFixed(1)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

---

## Phase 2: Customer Management (Day 2)

**Goal:** Searchable, filterable, paginated customer list

**Time Estimate:** 4-6 hours

### Step 2.1: Create Customer List Hook (1 hour)

**File:** `src/hooks/useCustomers.ts`

```typescript
import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_BASE_URL;

interface Customer {
  tenant_id: number;
  email: string;
  company_name: string;
  tier: string;
  status: string;
  created_at: string;
  records: number;
  storage_gb: number;
  mrr: number;
  stripe_customer_id: string;
}

interface CustomerFilters {
  tier?: string;
  status?: string;
  sort?: string;
  page?: number;
  limit?: number;
}

export function useCustomers(filters: CustomerFilters = {}) {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchCustomers();
  }, [filters.tier, filters.status, filters.sort, filters.page]);

  const fetchCustomers = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('authToken');
      const params = new URLSearchParams();

      if (filters.tier) params.append('tier', filters.tier);
      if (filters.status) params.append('status', filters.status);
      if (filters.sort) params.append('sort', filters.sort);
      if (filters.page) params.append('page', filters.page.toString());
      if (filters.limit) params.append('limit', filters.limit.toString());

      const response = await axios.get(
        `${API_URL}/admin/analytics/customers?${params}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setCustomers(response.data.customers);
      setTotal(response.data.total);
      setPages(response.data.pages);
    } catch (err) {
      console.error('Failed to fetch customers:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return { customers, total, pages, isLoading, refetch: fetchCustomers };
}
```

---

### Step 2.2: Create Customer List Page (2 hours)

**File:** `src/pages/admin/CustomersPage.tsx`

```typescript
import { useState } from 'react';
import { useCustomers } from '@/hooks/useCustomers';
import { useSearchParams } from 'react-router-dom';

export default function CustomersPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  const filters = {
    tier: searchParams.get('tier') || undefined,
    status: searchParams.get('status') || 'active',
    sort: searchParams.get('sort') || 'created_desc',
    page: parseInt(searchParams.get('page') || '1')
  };

  const { customers, total, pages, isLoading } = useCustomers(filters);

  const updateFilter = (key: string, value: string) => {
    const newParams = new URLSearchParams(searchParams);
    if (value) {
      newParams.set(key, value);
    } else {
      newParams.delete(key);
    }
    newParams.set('page', '1'); // Reset to page 1 on filter change
    setSearchParams(newParams);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Customers</h1>
        <p className="text-gray-600">{total} total customers</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Tier Filter */}
          <select
            value={filters.tier || ''}
            onChange={(e) => updateFilter('tier', e.target.value)}
            className="border rounded px-3 py-2"
          >
            <option value="">All Tiers</option>
            <option value="free">Free</option>
            <option value="starter">Starter</option>
            <option value="business">Business</option>
            <option value="enterprise">Enterprise</option>
          </select>

          {/* Status Filter */}
          <select
            value={filters.status || 'active'}
            onChange={(e) => updateFilter('status', e.target.value)}
            className="border rounded px-3 py-2"
          >
            <option value="">All Statuses</option>
            <option value="active">Active</option>
            <option value="suspended">Suspended</option>
            <option value="read_only">Read Only</option>
            <option value="cancelled">Cancelled</option>
          </select>

          {/* Sort */}
          <select
            value={filters.sort || 'created_desc'}
            onChange={(e) => updateFilter('sort', e.target.value)}
            className="border rounded px-3 py-2"
          >
            <option value="created_desc">Newest First</option>
            <option value="created_asc">Oldest First</option>
            <option value="usage_desc">Highest Usage</option>
            <option value="revenue_desc">Highest Revenue</option>
          </select>

          {/* Clear Filters */}
          <button
            onClick={() => setSearchParams({})}
            className="border border-gray-300 rounded px-3 py-2 hover:bg-gray-50"
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Customer Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tier</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Usage</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">MRR</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Joined</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {customers.map((customer) => (
              <tr key={customer.tenant_id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div>
                    <p className="font-medium text-gray-900">{customer.company_name || 'No company'}</p>
                    <p className="text-sm text-gray-500">{customer.email}</p>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs font-semibold rounded ${getTierBadgeClass(customer.tier)}`}>
                    {customer.tier}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs font-semibold rounded ${getStatusBadgeClass(customer.status)}`}>
                    {customer.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm">
                  <div className="space-y-1">
                    <p>{customer.records.toLocaleString()} records</p>
                    <p className="text-gray-500">{customer.storage_gb.toFixed(2)} GB</p>
                  </div>
                </td>
                <td className="px-6 py-4 font-medium">
                  ${customer.mrr.toFixed(2)}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {new Date(customer.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-600">
          Page {filters.page} of {pages}
        </p>
        <div className="flex gap-2">
          <button
            disabled={filters.page === 1}
            onClick={() => updateFilter('page', (filters.page - 1).toString())}
            className="px-4 py-2 border rounded disabled:opacity-50"
          >
            Previous
          </button>
          <button
            disabled={filters.page === pages}
            onClick={() => updateFilter('page', (filters.page + 1).toString())}
            className="px-4 py-2 border rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}

function getTierBadgeClass(tier: string) {
  const classes = {
    free: 'bg-gray-100 text-gray-800',
    starter: 'bg-blue-100 text-blue-800',
    business: 'bg-purple-100 text-purple-800',
    enterprise: 'bg-green-100 text-green-800'
  };
  return classes[tier as keyof typeof classes] || classes.free;
}

function getStatusBadgeClass(status: string) {
  const classes = {
    active: 'bg-green-100 text-green-800',
    suspended: 'bg-red-100 text-red-800',
    read_only: 'bg-yellow-100 text-yellow-800',
    cancelled: 'bg-gray-100 text-gray-800'
  };
  return classes[status as keyof typeof classes] || classes.active;
}
```

**Add Route:**
```typescript
{
  path: '/admin/analytics/customers',
  element: <ProtectedRoute roles={['admin']}><CustomersPage /></ProtectedRoute>
}
```

---

## Phase 3: Revenue Analytics (Day 3)

**Goal:** Revenue charts and trend analysis

**Time Estimate:** 3-4 hours

### Step 3.1: Create Revenue Hook (30 min)

**File:** `src/hooks/useRevenue.ts`

```typescript
import { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_BASE_URL;

interface RevenueData {
  mrr: number;
  arr: number;
  by_tier: Record<string, number>;
  monthly_trend: Array<{ month: string; revenue: number }>;
  churn_rate: number;
  estimated_ltv: number;
}

export function useRevenue() {
  const [revenue, setRevenue] = useState<RevenueData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchRevenue();
  }, []);

  const fetchRevenue = async () => {
    try {
      const token = localStorage.getItem('authToken');
      const response = await axios.get(`${API_URL}/admin/analytics/revenue`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRevenue(response.data);
    } catch (err) {
      console.error('Failed to fetch revenue:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return { revenue, isLoading, refetch: fetchRevenue };
}
```

---

### Step 3.2: Create Revenue Chart Component (2 hours)

**File:** `src/components/analytics/RevenueChart.tsx`

```typescript
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface RevenueChartProps {
  data: Array<{ month: string; revenue: number }>;
}

export default function RevenueChart({ data }: RevenueChartProps) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-bold mb-4">Revenue Trend (6 Months)</h2>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="month" />
          <YAxis tickFormatter={(value) => `$${value.toLocaleString()}`} />
          <Tooltip formatter={(value: number) => `$${value.toLocaleString()}`} />
          <Legend />
          <Line
            type="monotone"
            dataKey="revenue"
            stroke="#3B82F6"
            strokeWidth={2}
            name="Monthly Revenue"
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Growth Indicator */}
      <div className="mt-4 pt-4 border-t">
        {data.length >= 2 && (
          <div className="flex items-center gap-2">
            {(() => {
              const growth = ((data[data.length - 1].revenue - data[data.length - 2].revenue) / data[data.length - 2].revenue) * 100;
              const isPositive = growth > 0;
              return (
                <>
                  <span className={`text-2xl ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                    {isPositive ? '↗' : '↘'}
                  </span>
                  <p className="text-sm">
                    <span className={`font-bold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                      {Math.abs(growth).toFixed(1)}%
                    </span>
                    <span className="text-gray-600 ml-1">month-over-month</span>
                  </p>
                </>
              );
            })()}
          </div>
        )}
      </div>
    </div>
  );
}
```

---

### Step 3.3: Create Revenue Page (1 hour)

**File:** `src/pages/admin/RevenuePage.tsx`

```typescript
import { useRevenue } from '@/hooks/useRevenue';
import RevenueChart from '@/components/analytics/RevenueChart';

export default function RevenuePage() {
  const { revenue, isLoading } = useRevenue();

  if (isLoading) return <LoadingSpinner />;
  if (!revenue) return <div>Failed to load revenue data</div>;

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Revenue Analytics</h1>

      {/* Key Revenue Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-600">Monthly Recurring Revenue</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">${revenue.mrr.toLocaleString()}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-600">Annual Recurring Revenue</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">${revenue.arr.toLocaleString()}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-600">Churn Rate</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{revenue.churn_rate.toFixed(1)}%</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-600">Customer LTV</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">${revenue.estimated_ltv.toFixed(0)}</p>
        </div>
      </div>

      {/* Revenue Chart */}
      <RevenueChart data={revenue.monthly_trend} />

      {/* Revenue by Tier */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Revenue by Tier</h2>
        <div className="space-y-3">
          {Object.entries(revenue.by_tier).map(([tier, amount]) => (
            <div key={tier} className="flex items-center justify-between">
              <span className="capitalize font-medium">{tier}</span>
              <div className="flex items-center gap-4">
                <div className="w-64 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${(amount / revenue.mrr) * 100}%` }}
                  />
                </div>
                <span className="font-bold w-24 text-right">${amount.toLocaleString()}</span>
                <span className="text-sm text-gray-600 w-16 text-right">
                  {((amount / revenue.mrr) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

**Add Route:**
```typescript
{
  path: '/admin/analytics/revenue',
  element: <ProtectedRoute roles={['admin']}><RevenuePage /></ProtectedRoute>
}
```

---

## API Reference

All endpoints require `Authorization: Bearer <JWT_TOKEN>` header with admin role.

### GET /api/admin/analytics/overview

**Response:**
```json
{
  "total_tenants": 1247,
  "by_tier": {
    "free": 892,
    "starter": 287,
    "business": 58,
    "enterprise": 10
  },
  "active_tenants": 1185,
  "suspended_tenants": 62,
  "mrr": 18453.13,
  "signups_last_30_days": 143
}
```

### GET /api/admin/analytics/tiers

**Response:**
```json
{
  "tiers": [
    {
      "tier": "starter",
      "count": 287,
      "revenue": 4302.13,
      "avg_usage_percent": 67.5,
      "avg_records": 1250,
      "churned_last_month": 12
    }
  ]
}
```

### GET /api/admin/analytics/usage

**Response:**
```json
{
  "approaching_limits": [
    {
      "tenant_id": 1025,
      "email": "acme@example.com",
      "company_name": "Acme Corp",
      "tier": "starter",
      "quota_type": "records",
      "used": 4850,
      "limit": 5000,
      "percent_used": 97
    }
  ],
  "total_at_risk": 45
}
```

### GET /api/admin/analytics/customers

**Query Parameters:**
- `tier` - Filter by tier (free, starter, business, enterprise)
- `status` - Filter by status (active, suspended, read_only, cancelled)
- `sort` - Sort by (created_asc, created_desc, usage_desc, revenue_desc)
- `page` - Page number (default 1)
- `limit` - Items per page (default 25, max 100)

**Response:**
```json
{
  "customers": [
    {
      "tenant_id": 1025,
      "email": "acme@example.com",
      "company_name": "Acme Corp",
      "tier": "starter",
      "status": "active",
      "created_at": "2025-12-15T10:30:00",
      "records": 4850,
      "storage_bytes": 1932735283,
      "storage_gb": 1.8,
      "mrr": 14.99,
      "stripe_customer_id": "cus_..."
    }
  ],
  "total": 287,
  "page": 1,
  "limit": 25,
  "pages": 12
}
```

### GET /api/admin/analytics/revenue

**Response:**
```json
{
  "mrr": 18453.13,
  "arr": 221437.56,
  "by_tier": {
    "starter": 4302.13,
    "business": 4582.00,
    "enterprise": 4990.00
  },
  "monthly_trend": [
    {"month": "2025-07", "revenue": 12345.67},
    {"month": "2025-08", "revenue": 13456.78},
    {"month": "2025-09", "revenue": 14567.89},
    {"month": "2025-10", "revenue": 15678.90},
    {"month": "2025-11", "revenue": 16789.01},
    {"month": "2025-12", "revenue": 18453.13}
  ],
  "churn_rate": 4.2,
  "estimated_ltv": 350.75
}
```

### GET /api/admin/analytics/health

**Response:**
```json
{
  "failed_payments_count": 12,
  "suspended_count": 8,
  "revenue_at_risk": 647.92,
  "high_value_customers": [
    {
      "tenant_id": 1234,
      "email": "bigco@example.com",
      "company_name": "BigCo Inc",
      "tier": "enterprise",
      "mrr": 499
    }
  ],
  "upsell_opportunities": [
    {
      "tenant_id": 1052,
      "email": "growth@startup.com",
      "company_name": "Growth Startup",
      "current_tier": "starter",
      "suggested_tier": "business",
      "usage_percent": 94.2
    }
  ]
}
```

---

## Component Architecture

### Recommended File Structure

```
src/
├── pages/
│   └── admin/
│       ├── AnalyticsPage.tsx        # Main dashboard
│       ├── CustomersPage.tsx        # Customer list
│       └── RevenuePage.tsx          # Revenue analytics
├── components/
│   └── analytics/
│       ├── MetricsGrid.tsx          # Key metrics cards
│       ├── HealthAlerts.tsx         # Alerts widget
│       ├── TierChart.tsx            # Pie chart
│       ├── RevenueChart.tsx         # Line chart
│       └── CustomerTable.tsx        # Reusable table (optional)
└── hooks/
    ├── useAnalytics.ts              # Overview + health
    ├── useCustomers.ts              # Customer list
    └── useRevenue.ts                # Revenue data
```

---

## Testing Checklist

### Phase 1 Tests

- [ ] Analytics page loads without errors
- [ ] Metrics display correct values from API
- [ ] Health alerts show when there are issues
- [ ] Tier chart renders with correct percentages
- [ ] Page requires admin role (403 for non-admin)

### Phase 2 Tests

- [ ] Customer list loads and paginates
- [ ] Tier filter works (free, starter, business, enterprise)
- [ ] Status filter works (active, suspended, etc.)
- [ ] Sort options work (created, usage, revenue)
- [ ] Pagination buttons work correctly
- [ ] Clear filters button resets all filters

### Phase 3 Tests

- [ ] Revenue chart displays 6-month trend
- [ ] MRR, ARR, churn rate display correctly
- [ ] Revenue by tier bars show correct percentages
- [ ] Growth indicator shows correct month-over-month change

### General Tests

- [ ] All API calls include JWT token
- [ ] Error states handle gracefully
- [ ] Loading states display spinners
- [ ] Mobile responsive design works
- [ ] Colors match brand guidelines

---

## Tips for Implementation

### 1. Error Handling

Always handle API errors gracefully:

```typescript
try {
  const response = await axios.get(...);
  setData(response.data);
} catch (err: any) {
  if (err.response?.status === 403) {
    // User doesn't have admin role
    navigate('/dashboard');
  } else {
    toast.error('Failed to load analytics');
  }
}
```

### 2. Loading States

Show spinners while data loads:

```typescript
if (isLoading) {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
    </div>
  );
}
```

### 3. Refresh Button

Add a refresh button to analytics:

```typescript
<button onClick={refetch} className="btn">
  🔄 Refresh
</button>
```

### 4. Real-Time Updates

Consider polling for updates every 5 minutes:

```typescript
useEffect(() => {
  const interval = setInterval(fetchAnalytics, 5 * 60 * 1000);
  return () => clearInterval(interval);
}, []);
```

---

## Questions?

**Backend API:** All endpoints are live at `http://localhost:8000/api/admin/analytics/*`

**Testing:** Login as `admin@pathsix.local` / `PathSix2025!` to test with admin role

**Issues:** Check browser console for API errors, verify JWT token includes admin role

---

**Last Updated:** January 2026
**Backend Version:** 2.0 (Tiered Pricing Edition)

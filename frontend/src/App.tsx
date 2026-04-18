import React from "react";
import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "./components/ui/toaster";
import { TooltipProvider } from "./components/ui/tooltip";
import { SidebarProvider, SidebarTrigger } from "./components/ui/sidebar";
import { AppSidebar } from "./components/app-sidebar";
import { ThemeToggle } from "./components/theme-toggle";
import Dashboard from "./pages/dashboard";
import Sensors from "./pages/sensors";
import SensorDetail from "./pages/sensor-detail";
import Interventions from "./pages/interventions";
import Citizens from "./pages/citizens";
import Vehicles from "./pages/vehicles";
import Technicians from "./pages/technicians";
import Analytics from "./pages/analytics";
import NotFound from "./pages/not-found";

function Router() {
  return (
    <Switch>
      <Route path="/" component={Dashboard} />
      <Route path="/sensors" component={Sensors} />
      <Route path="/sensors/:id" component={SensorDetail} />
      <Route path="/interventions" component={Interventions} />
      <Route path="/citizens" component={Citizens} />
      <Route path="/vehicles" component={Vehicles} />
      <Route path="/technicians" component={Technicians} />
      <Route path="/analytics" component={Analytics} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  const style = {
    "--sidebar-width": "16rem",
    "--sidebar-width-icon": "3rem",
  };

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <SidebarProvider style={style as React.CSSProperties}>
          <div className="flex h-screen w-full">
            <AppSidebar />
            <div className="flex flex-col flex-1">
              <header className="flex items-center justify-between p-4 border-b border-border sticky top-0 bg-background z-10">
                <SidebarTrigger data-testid="button-sidebar-toggle" />
                <ThemeToggle />
              </header>
              <main className="flex-1 overflow-auto">
                <Router />
              </main>
            </div>
          </div>
        </SidebarProvider>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;

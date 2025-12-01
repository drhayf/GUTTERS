/**
 * Settings Index Screen
 */
import React from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  Pressable, 
  ScrollView,
  Platform 
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Link } from 'expo-router';
import { ChevronRight, Brain, Cpu, Palette, Database, Info, User, Layers } from '@tamagui/lucide-icons';

interface SettingsItemProps {
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  href: string;
  iconBgColor: string;
}

function SettingsItem({ icon, title, subtitle, href, iconBgColor }: SettingsItemProps) {
  return (
    <Link href={href as any} asChild>
      <Pressable>
        {({ pressed }) => (
          <View style={[styles.settingsItem, pressed && styles.settingsItemPressed]}>
            <View style={[styles.iconContainer, { backgroundColor: iconBgColor }]}>
              {icon}
            </View>
            
            <View style={styles.settingsItemContent}>
              <Text style={styles.settingsItemTitle}>{title}</Text>
              <Text style={styles.settingsItemSubtitle}>{subtitle}</Text>
            </View>
            
            <ChevronRight size={20} color="rgba(255,255,255,0.4)" />
          </View>
        )}
      </Pressable>
    </Link>
  );
}

function Separator() {
  return <View style={styles.separator} />;
}

export default function SettingsScreen() {
  return (
    <SafeAreaView style={styles.safeArea} edges={['bottom']}>
      <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Settings</Text>
          <Text style={styles.headerSubtitle}>Configure your AI experience</Text>
        </View>
        
        {/* Settings Card */}
        <View style={styles.card}>
          <SettingsItem
            icon={<Brain size={24} color="#A855F7" />}
            iconBgColor="rgba(147, 51, 234, 0.15)"
            title="Reasoning Engine"
            subtitle="Configure HRM thinking depth"
            href="/settings/hrm"
          />
          
          <Separator />
          
          <SettingsItem
            icon={<Cpu size={24} color="#06B6D4" />}
            iconBgColor="rgba(6, 182, 212, 0.15)"
            title="AI Models"
            subtitle="Primary, Fast, and Synthesis models"
            href="/settings/models"
          />
          
          <Separator />
          
          <SettingsItem
            icon={<Layers size={24} color="#A855F7" />}
            iconBgColor="rgba(168, 85, 247, 0.15)"
            title="Modules"
            subtitle="Enable or disable capabilities"
            href="/settings/modules"
          />
          
          <Separator />
          
          <SettingsItem
            icon={<Palette size={24} color="#EC4899" />}
            iconBgColor="rgba(236, 72, 153, 0.15)"
            title="Appearance"
            subtitle="Theme and visual settings"
            href="/(tabs)"
          />
          
          <Separator />
          
          <SettingsItem
            icon={<User size={24} color="#F59E0B" />}
            iconBgColor="rgba(245, 158, 11, 0.15)"
            title="Saved Profiles"
            subtitle="Manage your Digital Twin profiles"
            href="/settings/profiles"
          />
          
          <Separator />
          
          <SettingsItem
            icon={<Database size={24} color="#10B981" />}
            iconBgColor="rgba(16, 185, 129, 0.15)"
            title="Data & Privacy"
            subtitle="Manage your data"
            href="/(tabs)"
          />
        </View>
        
        {/* Footer */}
        <View style={styles.footer}>
          <View style={styles.footerContent}>
            <Info size={16} color="rgba(255,255,255,0.4)" />
            <Text style={styles.footerText}>Project Sovereign v0.1.0</Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#050505',
  },
  container: {
    flex: 1,
    backgroundColor: '#050505',
  },
  contentContainer: {
    paddingBottom: 32,
  },
  header: {
    padding: 16,
    paddingTop: 8,
  },
  headerTitle: {
    fontSize: 32,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 8,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  headerSubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.5)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  card: {
    margin: 16,
    backgroundColor: '#0A0A0A',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    overflow: 'hidden',
  },
  settingsItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    gap: 12,
  },
  settingsItemPressed: {
    opacity: 0.7,
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
  },
  iconContainer: {
    width: 44,
    height: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  settingsItemContent: {
    flex: 1,
  },
  settingsItemTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 2,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  settingsItemSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.5)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  separator: {
    height: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    marginLeft: 72,
  },
  footer: {
    flex: 1,
    justifyContent: 'flex-end',
    paddingTop: 32,
  },
  footerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: 16,
  },
  footerText: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.4)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
});

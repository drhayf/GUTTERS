import React, { useState, useCallback } from 'react';
import { RefreshControl, Alert, Platform, Linking, StyleSheet, View, Text as RNText, Pressable } from 'react-native';
import { ScrollView } from 'react-native';
import { Trash2, Download, Play, Save, Plus, X, ChevronRight } from '@tamagui/lucide-icons';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiClient, ProfileSlot } from '../../lib/api-client';

const GENESIS_SESSION_KEY = '@sovereign/genesis_session';

export default function ProfilesScreen() {
  const router = useRouter();
  const [profiles, setProfiles] = useState<ProfileSlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [maxSlots, setMaxSlots] = useState(10);

  // Load profiles on mount
  React.useEffect(() => {
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
    try {
      setLoading(true);
      const response = await apiClient.listProfiles();
      setProfiles(response.profiles);
      setMaxSlots(response.max_slots);
    } catch (error) {
      console.error('Failed to load profiles:', error);
      Alert.alert('Error', 'Failed to load profiles');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadProfiles();
    setRefreshing(false);
  }, []);

  const handleResume = async (slotId: string, profileName: string, status: string, totalResponses: number) => {
    try {
      setLoading(true);
      
      // First load the full profile data
      const loadResponse = await apiClient.loadProfile(slotId);
      
      if (!loadResponse.success) {
        Alert.alert('Error', loadResponse.message);
        return;
      }
      
      // Build session object to store locally
      const responses = loadResponse.session_state?.responses || [];
      const sessionData = {
        sessionId: loadResponse.session_state?.session_id || slotId,
        phase: loadResponse.session_state?.phase || 'activation',
        questionIndex: totalResponses,
        responses: responses as Array<{ question: string; response: string; phase: string }>,
        lastPayload: loadResponse.session_state?.last_payload || null,
        profileComplete: status === 'completed' || totalResponses >= 25,
        digitalTwin: loadResponse.digital_twin || null, // Store Digital Twin for recovery
        createdAt: new Date().toISOString(),
      };
      
      // Save to local AsyncStorage so Genesis can pick it up
      await AsyncStorage.setItem(GENESIS_SESSION_KEY, JSON.stringify(sessionData));
      console.log('[Profiles] Saved session to AsyncStorage:', {
        sessionId: sessionData.sessionId,
        responses: Array.isArray(responses) ? responses.length : 0,
        profileComplete: sessionData.profileComplete,
        hasDigitalTwin: !!sessionData.digitalTwin,
      });
      
      // Now resume the profile in backend
      const resumeResponse = await apiClient.resumeProfile(slotId);
      
      if (resumeResponse.success) {
        // Navigate to Genesis with the restored session
        router.push({
          pathname: '/genesis',
          params: {
            session_id: resumeResponse.session_id,
            restored: 'true',
            profile_name: profileName,
          },
        });
      } else {
        Alert.alert('Error', resumeResponse.message);
      }
    } catch (error) {
      console.error('Failed to resume profile:', error);
      Alert.alert('Error', 'Failed to resume profile');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = (slotId: string, profileName: string) => {
    Alert.alert(
      'Delete Profile',
      `Are you sure you want to delete "${profileName}"? This cannot be undone.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await apiClient.deleteProfile(slotId);
              setProfiles(profiles.filter(p => p.slot_id !== slotId));
            } catch (error) {
              console.error('Failed to delete profile:', error);
              Alert.alert('Error', 'Failed to delete profile');
            }
          },
        },
      ]
    );
  };

  const handleDownload = async (slotId: string) => {
    try {
      const url = apiClient.getProfileDownloadUrl(slotId);
      
      if (Platform.OS === 'web') {
        // On web, open download URL in new tab
        window.open(url, '_blank');
      } else {
        // On mobile, use Linking
        await Linking.openURL(url);
      }
    } catch (error) {
      console.error('Failed to download profile:', error);
      Alert.alert('Error', 'Failed to download profile');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return '#10B981';
      case 'in_progress':
        return '#F59E0B';
      case 'archived':
        return 'rgba(255,255,255,0.4)';
      default:
        return '#3B82F6';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed':
        return '✓ Complete';
      case 'in_progress':
        return '⟳ In Progress';
      case 'archived':
        return '📦 Archived';
      default:
        return status;
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  if (loading && profiles.length === 0) {
    return (
      <View style={styles.loadingContainer}>
        <RNText style={styles.loadingText}>Loading profiles...</RNText>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        contentContainerStyle={styles.scrollContent}
      >
        {/* Header */}
        <View style={styles.header}>
          <RNText style={styles.headerTitle}>Saved Profiles</RNText>
          <RNText style={styles.headerSubtitle}>
            {profiles.length} of {maxSlots} slots used
          </RNText>
        </View>

        <View style={styles.separator} />

        {/* New Profile Button */}
        <Pressable
          style={styles.newButton}
          onPress={() => router.push('/genesis')}
        >
          <Plus size={20} color="#FFFFFF" />
          <RNText style={styles.newButtonText}>Start New Profile</RNText>
        </Pressable>

        {/* Profile List */}
        {profiles.length === 0 ? (
          <View style={styles.emptyCard}>
            <RNText style={styles.emptyEmoji}>🌱</RNText>
            <RNText style={styles.emptyTitle}>No Saved Profiles</RNText>
            <RNText style={styles.emptyText}>
              Complete the Genesis profiling to create your first Digital Twin profile.
            </RNText>
          </View>
        ) : (
          <View style={styles.profileList}>
            {profiles.map((profile) => (
              <View key={profile.slot_id} style={styles.profileCard}>
                {/* Profile Header */}
                <View style={styles.profileHeader}>
                  <View style={styles.profileTitleContainer}>
                    <RNText style={styles.profileName}>{profile.name}</RNText>
                    <RNText style={[styles.profileStatus, { color: getStatusColor(profile.status) }]}>
                      {getStatusLabel(profile.status)}
                    </RNText>
                  </View>
                  <RNText style={styles.slotId}>
                    {profile.slot_id.replace('slot_', '#')}
                  </RNText>
                </View>

                {/* Progress Bar */}
                <View style={styles.progressSection}>
                  <View style={styles.progressLabels}>
                    <RNText style={styles.phaseLabel}>
                      {profile.phase.charAt(0).toUpperCase() + profile.phase.slice(1)}
                    </RNText>
                    <RNText style={styles.percentLabel}>
                      {profile.completion_percentage.toFixed(0)}%
                    </RNText>
                  </View>
                  <View style={styles.progressBar}>
                    <View
                      style={[
                        styles.progressFill,
                        {
                          width: `${profile.completion_percentage}%`,
                          backgroundColor: profile.status === 'completed' ? '#10B981' : '#9333EA',
                        },
                      ]}
                    />
                  </View>
                </View>

                {/* Summary */}
                {profile.summary && (
                  <RNText style={styles.summary} numberOfLines={2}>
                    {profile.summary}
                  </RNText>
                )}

                {/* Metadata */}
                <View style={styles.metadata}>
                  <RNText style={styles.metaText}>
                    {profile.total_responses} responses
                  </RNText>
                  <RNText style={styles.metaText}>
                    Updated {formatDate(profile.updated_at)}
                  </RNText>
                </View>

                <View style={styles.cardSeparator} />

                {/* Actions */}
                <View style={styles.actions}>
                  <Pressable
                    style={[styles.actionButton, styles.deleteButton]}
                    onPress={() => handleDelete(profile.slot_id, profile.name)}
                  >
                    <Trash2 size={16} color="#EF4444" />
                    <RNText style={styles.deleteButtonText}>Delete</RNText>
                  </Pressable>
                  <Pressable
                    style={styles.actionButton}
                    onPress={() => handleDownload(profile.slot_id)}
                  >
                    <Download size={16} color="rgba(255,255,255,0.7)" />
                    <RNText style={styles.actionButtonText}>Export</RNText>
                  </Pressable>
                  <Pressable
                    style={[styles.actionButton, styles.resumeButton]}
                    onPress={() => handleResume(profile.slot_id, profile.name, profile.status, profile.total_responses)}
                  >
                    <Play size={16} color="#FFFFFF" />
                    <RNText style={styles.resumeButtonText}>
                      {profile.status === 'completed' ? 'View' : 'Resume'}
                    </RNText>
                  </Pressable>
                </View>
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#050505',
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#050505',
  },
  loadingText: {
    color: 'rgba(255,255,255,0.6)',
    fontSize: 14,
    marginTop: 12,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 32,
  },
  header: {
    marginBottom: 16,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.5)',
  },
  separator: {
    height: 1,
    backgroundColor: 'rgba(255,255,255,0.1)',
    marginVertical: 16,
  },
  newButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#9333EA',
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 12,
    marginBottom: 20,
    gap: 8,
  },
  newButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  emptyCard: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 16,
    padding: 32,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  emptyEmoji: {
    fontSize: 40,
    marginBottom: 12,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: 'rgba(255,255,255,0.7)',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.4)',
    textAlign: 'center',
  },
  profileList: {
    gap: 12,
  },
  profileCard: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  profileHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  profileTitleContainer: {
    flex: 1,
    marginRight: 8,
  },
  profileName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FFFFFF',
    marginBottom: 2,
  },
  profileStatus: {
    fontSize: 12,
    fontWeight: '500',
  },
  slotId: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.4)',
  },
  progressSection: {
    marginBottom: 12,
  },
  progressLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  phaseLabel: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.5)',
  },
  percentLabel: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.5)',
  },
  progressBar: {
    height: 4,
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
  },
  summary: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.6)',
    marginBottom: 12,
  },
  metadata: {
    flexDirection: 'row',
    gap: 16,
    marginBottom: 12,
  },
  metaText: {
    fontSize: 11,
    color: 'rgba(255,255,255,0.4)',
  },
  cardSeparator: {
    height: 1,
    backgroundColor: 'rgba(255,255,255,0.1)',
    marginVertical: 12,
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 8,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    gap: 6,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.2)',
  },
  actionButtonText: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.7)',
  },
  deleteButton: {
    borderColor: 'rgba(239, 68, 68, 0.3)',
  },
  deleteButtonText: {
    fontSize: 13,
    color: '#EF4444',
  },
  resumeButton: {
    backgroundColor: '#9333EA',
    borderColor: '#9333EA',
  },
  resumeButtonText: {
    fontSize: 13,
    color: '#FFFFFF',
    fontWeight: '500',
  },
});

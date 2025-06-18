"use client";

import { Box, Button, LoadingOverlay, Stack, TextInput, Title, Text, Select, Textarea, Group, Progress, AspectRatio, ActionIcon, Badge, Divider } from "@mantine/core";
import { Container } from "@mantine/core";
import { Form, useForm } from "@mantine/form";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { notifications } from '@mantine/notifications';
import { ExerciseType, ExerciseTypeSchema } from "@/gen/web/shared/entities/v1/exercise_pb";
import { CameraView, CameraViewSchema, NewMedia } from "@/gen/web/shared/entities/v1/media_pb";
import { IconCross, IconPhoto, IconRefresh, IconTrash, IconUpload, IconX } from "@tabler/icons-react";
import { Dropzone, FileRejection } from "@mantine/dropzone";
import { AdminGatewayExerciseService } from "@/services";
import { ClientSelect } from "@/components/ClientSelect";
import { AssessmentSelect } from "@/components/AssessmentSelect";
import { formatLabel, toCameraView, toExerciseType } from "@/utils/string";
import { useListState, UseListStateHandlers } from "@mantine/hooks";
import { useQuery } from "@connectrpc/connect-query";
import { signMediaUpload } from "@/gen/web/gateways/admin/v1/admin_gateway-AdminGatewayService_connectquery";
import { StorageReference } from "@/gen/web/shared/messages/v1/media_pb";
import axios, { AxiosProgressEvent } from 'axios';

interface FormValues {
  name: string;
  client_id: string;
  assessment_id: string;
  description: string;
  comment: string;
  type: string;
}

type DropzoneFile = {
  file: File;
  size: number;
  upload_progress: number;
  camera_view: string;
  error: string | null;
  upload_url: string | null;
  storage_reference: StorageReference | null;
}

export default function NewExercisePage() {
  const router = useRouter();
  const [visible, setVisible] = useState(false);
  const [files, filesHandlers] = useListState<DropzoneFile>([]);

  const form = useForm<FormValues>({
    mode: 'uncontrolled',
    initialValues: {
      name: '',
      type: '',
      client_id: '',
      assessment_id: '',
      description: '',
      comment: '',
    },
  });

  const handleSubmit = async (values: FormValues) => {
    setVisible(true);
    try {
      const media: NewMedia[] = files.map(file => ({
        $typeName: 'shared.entities.v1.NewMedia',
        cameraView: toCameraView(file.camera_view),
        originalVideoLocation: file.upload_url!!,
        metadata: {
          file_name: file.file.name,
          file_size: file.file.size.toString(),
          file_type: file.file.type,
        }
      }));

      const response = await AdminGatewayExerciseService.createExercise({
        $typeName: 'shared.entities.v1.NewExercise',
        name: values.name,
        clientId: values.client_id,
        type: toExerciseType(values.type),
        ...(values.assessment_id ? { assessmentId: values.assessment_id } : {}),
        description: values.description,
        comment: values.comment,
      }, media);

      notifications.show({
        title: 'Success',
        message: 'Exercise created successfully',
        color: 'green',
      });

      router.push(`/app/exercises/${response.exercise?.exercise?.id}`);
    } catch (err) {
      notifications.show({
        title: 'Error',
        message: err instanceof Error ? err.message : 'An error occurred',
        color: 'red',
      });
    } finally {
      setVisible(false);
    }
  };

  const onDropzoneDrop = (files: File[]) => {
    for (const file of files) {
      filesHandlers.append({
        file,
        size: file.size,
        upload_progress: 0,
        camera_view: '',
        error: null,
        upload_url: null,
        storage_reference: null,
      });
    }
  }

  const handleFileUpload = async (idx: number, file: DropzoneFile, uploadUrl: string) => {
    filesHandlers.setItemProp(idx, 'upload_progress', 0);
    filesHandlers.setItemProp(idx, 'error', null);
    filesHandlers.setItemProp(idx, 'upload_url', null);
    filesHandlers.setItemProp(idx, 'storage_reference', null);

    try {
      await axios.put(uploadUrl, file.file, {
        onUploadProgress: (progressEvent: AxiosProgressEvent) => {
          filesHandlers.setItemProp(idx, 'upload_progress', Math.round((progressEvent.progress ?? 0) * 100));
        },
      });
      filesHandlers.setItemProp(idx, 'upload_progress', 100);
      filesHandlers.setItemProp(idx, 'storage_reference', file.storage_reference);
      filesHandlers.setItemProp(idx, 'upload_url', uploadUrl);
    } catch (err) {
      filesHandlers.setItemProp(idx, 'error', err instanceof Error ? err.message : 'Upload failed');
    }
  };

  const handleFileRemove = (idx: number) => {
    filesHandlers.remove(idx);
  };

  const handleCameraViewChange = (idx: number, value: string | null) => {
    if (value) {
      filesHandlers.setItemProp(idx, 'camera_view', value);
    }
  };

  const types = ExerciseTypeSchema.values.reduce((acc, value) => {
    if (value.localName.includes('UNSPECIFIED')) return acc;
    acc.push({
      value: value.localName,
      label: formatLabel(value.localName),
    });
    return acc;
  }, [] as { value: string, label: string }[])

  const onClientChange = (value: string | null) => {
    if (value) {
      form.setFieldValue('client_id', value);
    }
  }

  const onAssessmentChange = (value: string | null) => {
    if (value) {
      form.setFieldValue('assessment_id', value);
    }
  }

  return (
    <Container fluid>
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <Title order={2}>New Exercise</Title>
        <Box pos="relative">
          <LoadingOverlay visible={visible} zIndex={1000} overlayProps={{ blur: 2 }} />
          <Stack gap="md">
            <Group align="stretch" justify="space-between" wrap="wrap" gap="xl">
              <Stack w={{ base: '100%', md: '48%' }}>
                <TextInput label="Name" {...form.getInputProps('name')} required />
                <Textarea label="Description" {...form.getInputProps('description')} />
                <Textarea label="Comment" {...form.getInputProps('comment')} />
              </Stack>
              <Stack align="stretch" justify="space-between" w={{ base: '100%', md: '48%' }}>
                <Select label="Type" {...form.getInputProps('type')} required data={types} />
                <ClientSelect onChange={onClientChange} required />
                <AssessmentSelect disable={!form.values.client_id} onChange={onAssessmentChange} value={form.values.assessment_id} />
              </Stack>
            </Group>
            <Divider />
            <Dropzone
              onDrop={onDropzoneDrop}
              maxSize={10 * 1000 * 1000}
              accept={['video/*']}
              multiple
            >
              <Group justify="center" gap="xl" mih={220} style={{ pointerEvents: 'none' }}>
                <Dropzone.Accept>
                  <IconUpload size={52} color="var(--mantine-color-blue-6)" stroke={1.5} />
                </Dropzone.Accept>
                <Dropzone.Reject>
                  <IconX size={52} color="var(--mantine-color-red-6)" stroke={1.5} />
                </Dropzone.Reject>
                <Dropzone.Idle>
                  <IconPhoto size={52} color="var(--mantine-color-dimmed)" stroke={1.5} />
                </Dropzone.Idle>
                <div>
                  <Text size="xl" inline>
                    Drag video here or click to select files
                  </Text>
                  <Text size="sm" c="dimmed" inline mt={7}>
                    Attach as many files as you like, each file should not exceed 1 minutes and 10MB
                  </Text>
                </div>
              </Group>
            </Dropzone>
            <Divider />
            {files.length > 0 && (
              <Stack gap="md">
                {files.map((file, idx) => (
                  <Stack key={`${file.file.name}-${idx}`}>
                    <DropzoneFile
                      idx={idx}
                      file={file}
                      onUpload={handleFileUpload}
                      onRemove={handleFileRemove}
                      onCameraViewChange={handleCameraViewChange}
                    />
                    <Divider />
                  </Stack>
                ))}
              </Stack>
            )}
            {files.length > 0 && (
              <Button type="button" onClick={() => {
                filesHandlers.setState([]);
              }}>Clear Videos</Button>
            )}
            <Button type="submit" color="green" disabled={files.length === 0 || files.every(file => file.upload_progress !== 100)}>
              Create
            </Button>
          </Stack>
        </Box>
      </form>
    </Container>
  );
}

type DropzoneFileProps = {
  idx: number;
  file: DropzoneFile;
  onUpload: (idx: number, file: DropzoneFile, uploadUrl: string) => Promise<void>;
  onRemove: (idx: number) => void;
  onCameraViewChange: (idx: number, value: string | null) => void;
}

export function DropzoneFile({ idx, file, onUpload, onRemove, onCameraViewChange }: DropzoneFileProps) {
  const { data, isLoading, isError, error } = useQuery(signMediaUpload, {
    $typeName: 'shared.messages.v1.SignMediaUploadRequest',
    fileName: file.file.name,
    fileType: file.file.type,
    fileSize: BigInt(file.file.size),
  });

  useEffect(() => {
    if (!data || file.upload_progress === 100) return;
    onUpload(idx, file, data.uploadUrl);
  }, [data]);

  const cameraViews = CameraViewSchema.values.reduce((acc, value) => {
    if (value.localName.includes('UNSPECIFIED')) return acc;

    acc.push({
      value: value.localName,
      label: formatLabel(value.localName),
    });
    return acc;
  }, [] as { value: string, label: string }[]);

  return (
    <Stack gap="md" justify="center">
      <Group justify="space-between">
        <Text ta="center">{file.file.name}</Text>
        {file.error && <Text ta="center" c="red">{file.error}</Text>}
        <Group gap="md">
          <Badge variant="light" leftSection={<IconPhoto size={12} />} color={isLoading && !data ? 'yellow' : 'green'}>
            {isLoading && !data && 'Preparing to upload...'}
            {file.upload_progress < 100 && `Uploading ${file.upload_progress}%`}
            {file.error && 'Upload failed'}
            {file.upload_progress === 100 && 'Uploaded!'}
          </Badge>
          <ActionIcon onClick={() => onRemove(idx)} color="red">
            <IconTrash />
          </ActionIcon>
        </Group>
      </Group>
      <Group justify="space-between" align="stretch" wrap="wrap" gap="md">
        <Stack gap="md" w={{ base: '100%', sm: '45%' }}>
          <AspectRatio ratio={16 / 9}>
            <video
              controls
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            >
              <source src={URL.createObjectURL(file.file)} type={file.file.type} />
            </video>
          </AspectRatio>
        </Stack>
        <Stack gap="md" w={{ base: '100%', sm: '45%' }}>
          <Select
            label="Camera View"
            value={file.camera_view}
            onChange={(value) => onCameraViewChange(idx, value)}
            required
            data={cameraViews}
          />
        </Stack>
      </Group>
      <Progress value={file.upload_progress} />
    </Stack>
  );
}